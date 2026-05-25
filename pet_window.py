import sys
import ctypes
import random
import time
import traceback

from PySide6.QtCore import (
    Qt, QTimer, Signal, Slot, QPoint, QRect, 
    QEasingCurve, QSize, QCoreApplication, QMetaObject, Q_ARG, QThread
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPainterPath, QCursor, 
    QAction, QIcon, QPixmap, QGuiApplication, QKeyEvent
)
from PySide6.QtWidgets import (
    QWidget, QMenu, QSystemTrayIcon, QMessageBox, QApplication,
    QDialog, QLabel, QVBoxLayout, QHBoxLayout, QSlider, QCheckBox,
    QPushButton, QGroupBox, QFormLayout
)

from config import ConfigManager
from skins import get_skin, get_skin_info
from emotion_ai import EmotionAI
from animation_engine import AnimationEngine
from ui_components import SpeechBubble, ReminderDialog, SettingsDialog
from workers import WeatherWorker, ReminderWorker
from bongocat_renderer import BongocatRenderer
from action_state_machine import ActionStateMachine
from key_listener import ListenerThread


class PetWindow(QWidget):
    close_requested = Signal()
    
    def __init__(self, app: QApplication):
        print("[DEBUG] PetWindow.__init__ start")
        super().__init__()
        self._app = app
        
        self._dragging = False
        self._drag_offset = QPoint(0, 0)
        self._last_click_time = 0
        self._current_weather = None
        self._workers_started = False
        
        self._config = ConfigManager()
        self._emotion_ai = EmotionAI(self._config)
        self._emotion = self._emotion_ai.emotion or "happy"
        
        self._screen = app.primaryScreen().geometry()
        self._animation_engine = AnimationEngine(self._config, self._screen)
        
        self._bongocat_enabled = self._config.get("bongocat", "enabled") or False
        self._bongocat_renderer = BongocatRenderer()
        self._action_state_machine = ActionStateMachine()
        self._listener_thread = None
        self._ctrl_pressed = False
        
        self._setup_bongocat_connections()
        
        self._setup_window()
        self._skin = get_skin(self._config.get("pet", "current_skin") or "cat")
        self._setup_tray()
        self._setup_bubble()
        self._setup_signals()
        self._load_position()
        
        self._setup_ui_timer()
        QTimer.singleShot(500, self._start_delayed_workers)
        
        print("[DEBUG] PetWindow.__init__ done")
    
    def _setup_window(self):
        flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.NoFocus)
        
        scale = self._config.get("window", "scale") or 1.0
        if self._bongocat_enabled:
            base_w, base_h = 260, 220
        else:
            base_w, base_h = 120, 120
        width = int(base_w * scale)
        height = int(base_h * scale)
        self._config.set("window", "width", width)
        self._config.set("window", "height", height)
        self.setFixedSize(width, height)
        self.setWindowOpacity(self._config.get("window", "opacity") or 1.0)
        
        if self._config.get("window", "click_through") or self._bongocat_enabled:
            self._enable_click_through(True)
    
    def _setup_tray(self):
        pix = QPixmap(64, 64)
        pix.fill(QColor(0, 0, 0, 0))
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QBrush(QColor(255, 200, 150)))
        p.setPen(QPen(QColor(200, 150, 100), 2))
        p.drawEllipse(10, 15, 44, 44)
        p.drawEllipse(14, 5, 36, 32)
        p.end()
        
        self._tray = QSystemTrayIcon()
        self._tray.setIcon(QIcon(pix))
        self._tray.setToolTip("桌面宠物")
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()
    
    def _setup_bubble(self):
        self._bubble = SpeechBubble()
        self._bubble.show_message("你好呀！我来陪你啦~", 4000)
    
    def _setup_signals(self):
        self._emotion_ai.emotion_changed.connect(self._on_emotion_changed)
        self._emotion_ai.need_attention.connect(self._on_need_attention)
        self._emotion_ai.stats_changed.connect(self._on_stats_changed)
        
        self._animation_engine.action_changed.connect(self._on_action_changed)
        self._animation_engine.position_changed.connect(self._on_position_changed)
        self._animation_engine.frame_updated.connect(self._on_frame_updated)

    def _setup_bongocat_connections(self):
        am = self._action_state_machine
        am.left_paw_changed.connect(self._bongocat_renderer.update_left_paw)
        am.right_paw_changed.connect(self._bongocat_renderer.update_right_paw)
        am.mouse_state_changed.connect(self._bongocat_renderer.update_mouse)
        am.idle_state_changed.connect(self._bongocat_renderer.set_idle)
        
        self._bongocat_renderer.set_emotion(self._emotion)

        if self._bongocat_enabled:
            self._sync_bongocat_config()
            QTimer.singleShot(800, self._start_bongocat_listener)

    def _start_bongocat_listener(self):
        if self._listener_thread:
            return
        try:
            self._listener_thread = ListenerThread(self)
            listener = self._listener_thread.listener
            listener.key_pressed.connect(self._action_state_machine.on_key_press)
            listener.key_released.connect(self._action_state_machine.on_key_release)
            listener.mouse_clicked.connect(self._action_state_machine.on_mouse_click)
            listener.mouse_scrolled.connect(self._action_state_machine.on_mouse_scroll)
            listener.ctrl_pressed.connect(self._bongocat_ctrl_press)
            listener.ctrl_released.connect(self._bongocat_ctrl_release)
            self._listener_thread.start()
            print("[INFO] Bongocat keyboard/mouse listener started")
        except Exception as e:
            print(f"[ERROR] Failed to start Bongocat listener: {e}")
            self._listener_thread = None

    def _stop_bongocat_listener(self):
        if self._listener_thread:
            try:
                self._listener_thread.stop_listener()
                self._listener_thread = None
                print("[INFO] Bongocat listener stopped")
            except Exception as e:
                print(f"[ERROR] Failed to stop Bongocat listener: {e}")

    def _toggle_bongocat(self, enabled: bool):
        self._bongocat_enabled = enabled
        self._config.set("bongocat", "enabled", enabled)
        
        if enabled:
            self._sync_bongocat_config()
            self._start_bongocat_listener()
        else:
            self._stop_bongocat_listener()
        
        self._adjust_window_for_bongocat(enabled)
        self.update()

    def _sync_bongocat_config(self):
        bongo_cfg = self._config.get("bongocat")
        if bongo_cfg:
            params = {k: v for k, v in bongo_cfg.items() if k != "enabled"}
            self._action_state_machine.update_config(params)

    def _adjust_window_for_bongocat(self, enabled: bool):
        scale = self._config.get("window", "scale") or 1.0
        if enabled:
            base_w, base_h = 260, 220
        else:
            base_w, base_h = 120, 120
        
        width = int(base_w * scale)
        height = int(base_h * scale)
        self._config.set("window", "width", width)
        self._config.set("window", "height", height)
        self.setFixedSize(width, height)
        
        if enabled:
            self._enable_click_through(True)
            self._config.set("window", "click_through", True)
        else:
            self._enable_click_through(self._config.get("window", "click_through"))
    
    def _load_position(self):
        x = self._config.get("window", "x") or 500
        y = self._config.get("window", "y") or 300
        self.move(x, y)
        self._animation_engine.set_position(x, y)
    
    def _setup_ui_timer(self):
        self._ui_timer = QTimer(self)
        self._ui_timer.setInterval(50)
        self._ui_timer.timeout.connect(self.update)
        self._ui_timer.start()
    
    @Slot()
    def _start_delayed_workers(self):
        try:
            self._weather_worker = WeatherWorker(self._config)
            self._weather_worker.weather_ready.connect(self._on_weather_ready)
            self._weather_worker.weather_error.connect(self._on_worker_error)
            
            self._weather_thread = QThread(self)
            self._weather_worker.moveToThread(self._weather_thread)
            self._weather_thread.started.connect(self._weather_worker.start)
            self._weather_thread.start()
            
            reminders = self._config.get("reminders", "list") or []
            self._reminder_worker = ReminderWorker(reminders)
            self._reminder_worker.reminder_triggered.connect(self._on_reminder_triggered)
            
            self._reminder_thread = QThread(self)
            self._reminder_worker.moveToThread(self._reminder_thread)
            self._reminder_thread.started.connect(self._reminder_worker.start)
            self._reminder_thread.start()
            
            self._workers_started = True
            print("[DEBUG] Workers started")
        except Exception as e:
            print(f"[ERROR] Workers init: {e}")
    
    @Slot(str)
    def _on_emotion_changed(self, emotion: str):
        self._emotion = emotion
        self._animation_engine.set_emotion_context(emotion)
        self._bongocat_renderer.set_emotion(emotion)
        self.update()
    
    @Slot(str)
    def _on_need_attention(self, msg: str):
        if self._bubble:
            self._bubble.show_message(msg, 5000)
    
    @Slot(dict)
    def _on_stats_changed(self, stats: dict):
        pass
    
    @Slot(str)
    def _on_action_changed(self, action: str):
        self._current_action = action
        self.update()
    
    @Slot(int, int)
    def _on_position_changed(self, x: int, y: int):
        self.move(x, y)
        self._update_bubble_position()
    
    @Slot(float)
    def _on_frame_updated(self, frame: float):
        self._frame = frame

    def _bongocat_ctrl_press(self):
        if self._bongocat_enabled and not self._ctrl_pressed:
            self._ctrl_pressed = True
            self._enable_click_through(False)

    def _bongocat_ctrl_release(self):
        if self._bongocat_enabled and self._ctrl_pressed:
            self._ctrl_pressed = False
            self._enable_click_through(True)
    
    @Slot(dict)
    def _on_weather_ready(self, data: dict):
        self._current_weather = data
        desc = data.get("description", "")
        temp = data.get("temperature", "")
        if desc and temp:
            self._bubble.show_message(f"今天{desc}，气温{temp}", 6000)
    
    @Slot(str)
    def _on_worker_error(self, msg: str):
        print(f"[WARN] Worker: {msg}")
    
    @Slot(str)
    def _on_reminder_triggered(self, message: str):
        self._bubble.show_message(message, 6000)
        if self._tray:
            self._tray.showMessage("提醒", message, QSystemTrayIcon.Information, 5000)
    
    def _update_bubble_position(self):
        if self._bubble:
            geo = self.geometry()
            bx = geo.center().x() - self._bubble.width() // 2
            by = geo.y() - self._bubble.height() - 5
            self._bubble.move(bx, by)
    
    def _enable_click_through(self, enable: bool):
        try:
            hwnd = int(self.winId())
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020
            GWL_EXSTYLE = -20
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            if enable:
                style |= WS_EX_LAYERED | WS_EX_TRANSPARENT
            else:
                style &= ~WS_EX_TRANSPARENT
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        except Exception as e:
            print(f"[WARN] Click-through: {e}")
    
    def paintEvent(self, event):
        try:
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            p.setRenderHint(QPainter.SmoothPixmapTransform)
            
            rect = self.rect()
            
            if self._bongocat_enabled:
                self._bongocat_renderer.set_emotion(self._emotion)
                self._bongocat_renderer.set_frame(
                    getattr(self, '_frame', 0.0)
                )
                self._bongocat_renderer.set_action(
                    getattr(self._animation_engine, 'current_action', 'idle')
                )
                self._bongocat_renderer.draw(p, rect)
            else:
                action = getattr(self._animation_engine, 'current_action', 'idle')
                frame = getattr(self, '_frame', 0.0)
                self._skin.draw(p, rect, {}, self._emotion, action, frame)
            p.end()
        except Exception as e:
            print(f"[ERROR] paintEvent: {e}")
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._animation_engine.on_drag_start()
            self.raise_()
            self._emotion_ai.interact_click()
        elif event.button() == Qt.RightButton:
            self._show_menu(event.globalPosition().toPoint())
    
    def mouseMoveEvent(self, event):
        if self._dragging:
            np = event.globalPosition().toPoint() - self._drag_offset
            self.move(np)
            self._animation_engine.set_position(np.x(), np.y())
            self._update_bubble_position()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._dragging:
                self._dragging = False
                self._animation_engine.on_drag_end()
                self._config.set("window", "x", self.x())
                self._config.set("window", "y", self.y())
            
            ct = time.time()
            if ct - self._last_click_time < 0.3:
                self._last_click_time = 0
                self._animation_engine.on_double_click()
                self._show_stats()
            else:
                self._last_click_time = ct
                self._animation_engine.on_click()
    
    def _show_stats(self):
        stats = self._emotion_ai.get_stats()
        msg = f"体力: {stats['energy']:.0f}%\n心情: {stats['mood']:.0f}%\n饥饿: {stats['hunger']:.0f}%\n情绪: {self._emotion_name(stats['emotion'])}"
        self._bubble.show_message(msg, 4000)
    
    def _emotion_name(self, e: str) -> str:
        names = {
            'happy': '开心', 'neutral': '中性', 'bored': '无聊',
            'sleepy': '困倦', 'angry': '生气', 'shy': '害羞', 'hungry': '饥饿'
        }
        return names.get(e, e)
    
    def _show_menu(self, pos):
        menu = QMenu(self)
        
        stats = self._emotion_ai.get_stats()
        status_act = QAction(f"📊 状态 | 体力:{stats['energy']:.0f}% 心情:{stats['mood']:.0f}% 饥饿:{stats['hunger']:.0f}%", self)
        status_act.setEnabled(False)
        menu.addAction(status_act)
        menu.addSeparator()
        
        interact = menu.addMenu("🎮 互动")
        
        feed_act = QAction("🍖 喂食", self)
        feed_act.triggered.connect(self._on_feed)
        interact.addAction(feed_act)
        
        play_act = QAction("🎾 玩耍", self)
        play_act.triggered.connect(self._on_play)
        interact.addAction(play_act)
        
        if self._emotion != "sleepy":
            sleep_act = QAction("😴 让它睡觉", self)
            sleep_act.triggered.connect(self._on_sleep)
        else:
            sleep_act = QAction("☀️ 叫醒它", self)
            sleep_act.triggered.connect(self._on_wake)
        interact.addAction(sleep_act)
        
        talk_act = QAction("💬 让它说话", self)
        talk_act.triggered.connect(self._on_talk)
        interact.addAction(talk_act)
        
        sm = menu.addMenu("🎨 更换皮肤")
        si = get_skin_info()
        cs = self._config.get("pet", "current_skin")
        for sid, info in si.items():
            a = QAction(f"{info['emoji']} {info['name']}", self)
            a.setCheckable(True)
            a.setChecked(sid == cs)
            a.triggered.connect(lambda checked, s=sid: self._switch_skin(s))
            sm.addAction(a)
        
        menu.addSeparator()
        
        bongo_act = QAction("🐱 Bongocat模式", self)
        bongo_act.setCheckable(True)
        bongo_act.setChecked(self._bongocat_enabled)
        bongo_act.triggered.connect(lambda checked: self._toggle_bongocat(checked))
        menu.addAction(bongo_act)
        
        tools = menu.addMenu("⚙️ 设置")
        
        opacity_menu = tools.addMenu("🌫️ 透明度")
        for op in [100, 90, 80, 70, 60, 50, 40]:
            oa = QAction(f"{op}%", self)
            cur = int(self._config.get("window", "opacity") * 100)
            oa.setCheckable(True)
            oa.setChecked(op == cur)
            oa.triggered.connect(lambda checked, v=op: self._set_opacity(v / 100.0))
            opacity_menu.addAction(oa)
        
        scale_menu = tools.addMenu("🔍 缩放")
        for sc in [80, 100, 120, 150, 180]:
            sa = QAction(f"{sc}%", self)
            cur = int(self._config.get("window", "scale") * 100)
            sa.setCheckable(True)
            sa.setChecked(sc == cur)
            sa.triggered.connect(lambda checked, v=sc: self._set_scale(v / 100.0))
            scale_menu.addAction(sa)
        
        top_act = QAction("📌 窗口置顶", self)
        top_act.setCheckable(True)
        top_act.setChecked(self._config.get("window", "always_on_top"))
        top_act.triggered.connect(self._toggle_always_on_top)
        tools.addAction(top_act)
        
        settings_act = QAction("⚙️ 更多设置", self)
        settings_act.triggered.connect(self._open_settings)
        tools.addAction(settings_act)
        
        reminder_act = QAction("⏰ 定时提醒", self)
        reminder_act.triggered.connect(self._open_reminders)
        menu.addAction(reminder_act)
        
        if self._current_weather:
            weather_act = QAction(f"🌤️ {self._current_weather.get('temperature','')} {self._current_weather.get('description','')}", self)
            weather_act.setEnabled(False)
            menu.addAction(weather_act)
        
        menu.addSeparator()
        
        hide_act = QAction("👁️ 隐藏宠物", self)
        hide_act.triggered.connect(self.hide)
        menu.addAction(hide_act)
        
        quit_act = QAction("❌ 退出", self)
        quit_act.triggered.connect(self._quit)
        menu.addAction(quit_act)
        
        menu.exec(pos)
    
    @Slot()
    def _on_feed(self):
        self._emotion_ai.feed()
        foods = ["吃了个小鱼干，喵~", "真香！还要~", "吃饱了，嗝~", "美味！"]
        self._bubble.show_message(random.choice(foods), 3000)
    
    @Slot()
    def _on_play(self):
        self._emotion_ai.play()
        self._animation_engine.on_double_click()
        self._bubble.show_message("来玩追球球吧！", 3000)
    
    @Slot()
    def _on_sleep(self):
        self._emotion_ai.sleep()
        self._bubble.show_message("晚安~ zZZ", 2500)
    
    @Slot()
    def _on_wake(self):
        self._emotion_ai.wake()
        self._bubble.show_message("醒来啦！伸个懒腰~", 2500)
    
    @Slot()
    def _on_talk(self):
        msgs = [
            "主人在做什么呀~",
            "陪我玩一会儿嘛~",
            "我会一直陪着你的！",
            "你开心我就开心~",
            "今天也要加油哦！",
            "摸摸头~",
            "我好喜欢你呀~"
        ]
        self._bubble.show_message(random.choice(msgs), 3500)
    
    @Slot(str)
    def _switch_skin(self, sid: str):
        self._config.set("pet", "current_skin", sid)
        self._skin = get_skin(sid)
        self.update()
    
    @Slot(float)
    def _set_opacity(self, v: float):
        self._config.set("window", "opacity", v)
        self.setWindowOpacity(v)
    
    @Slot(float)
    def _set_scale(self, v: float):
        self._config.set("window", "scale", v)
        if self._bongocat_enabled:
            base_w, base_h = 260, 220
        else:
            base_w, base_h = 120, 120
        width = int(base_w * v)
        height = int(base_h * v)
        self._config.set("window", "width", width)
        self._config.set("window", "height", height)
        self.setFixedSize(width, height)
        self._bubble.show_message(f"缩放至 {int(v*100)}%", 2000)
    
    @Slot()
    def _toggle_always_on_top(self):
        cur = not self._config.get("window", "always_on_top")
        self._config.set("window", "always_on_top", cur)
        flags = Qt.FramelessWindowHint
        if cur:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()
        self._bubble.show_message("已置顶" if cur else "取消置顶", 2000)
    
    @Slot()
    def _open_settings(self):
        dlg = SettingsDialog(self._config, self)
        dlg.settings_changed.connect(self._apply_settings)
        dlg.exec()
    
    @Slot(dict)
    def _apply_settings(self, s: dict):
        if "window" in s:
            w = s["window"]
            if "scale" in w:
                self._config.set("window", "scale", w["scale"])
                if self._bongocat_enabled:
                    base_w, base_h = 260, 220
                else:
                    base_w, base_h = 120, 120
                self._config.set("window", "width", int(base_w * w["scale"]))
                self._config.set("window", "height", int(base_h * w["scale"]))
                self.setFixedSize(int(base_w * w["scale"]), int(base_h * w["scale"]))
            if "opacity" in w:
                self._config.set("window", "opacity", w["opacity"])
                self.setWindowOpacity(w["opacity"])
            if "edge_snap" in w:
                self._config.set("window", "edge_snap", w["edge_snap"])
            if "always_on_top" in w:
                self._config.set("window", "always_on_top", w["always_on_top"])
                flags = Qt.FramelessWindowHint
                if w["always_on_top"]:
                    flags |= Qt.WindowStaysOnTopHint
                self.setWindowFlags(flags)
                self.show()
            if "click_through" in w:
                self._config.set("window", "click_through", w["click_through"])
                self._enable_click_through(w["click_through"])
        if "pet" in s:
            if "auto_sleep" in s["pet"]:
                self._config.set("pet", "auto_sleep", s["pet"]["auto_sleep"])
    
    @Slot()
    def _open_reminders(self):
        cur = self._config.get("reminders", "list") or []
        dlg = ReminderDialog(cur, self)
        dlg.reminders_updated.connect(self._save_reminders)
        dlg.exec()
    
    @Slot(list)
    def _save_reminders(self, reminders: list):
        self._config.set("reminders", "list", reminders)
        if hasattr(self, '_reminder_worker') and self._reminder_worker:
            self._reminder_worker.update_reminders(reminders)
        self._bubble.show_message("提醒已更新", 2500)
    
    @Slot(QSystemTrayIcon.ActivationReason)
    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isHidden():
                self._safe_show()
            else:
                self.raise_()
        elif reason == QSystemTrayIcon.Context:
            self._show_menu(QCursor.pos())

    def _safe_show(self):
        self.show()
        self.raise_()
        self.activateWindow()
        
        flags = Qt.FramelessWindowHint
        if self._config.get("window", "always_on_top"):
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()
        
        if self._config.get("window", "click_through") or self._bongocat_enabled:
            self._enable_click_through(True)
    
    @Slot()
    def _quit(self):
        print("[DEBUG] Quitting...")
        self._config.set("window", "x", self.x())
        self._config.set("window", "y", self.y())
        
        self._stop_bongocat_listener()
        
        if self._workers_started:
            if hasattr(self, '_weather_worker') and self._weather_worker:
                self._weather_worker.stop()
            if hasattr(self, '_reminder_worker') and self._reminder_worker:
                self._reminder_worker.stop()
            if hasattr(self, '_weather_thread') and self._weather_thread:
                self._weather_thread.quit()
                self._weather_thread.wait(1000)
            if hasattr(self, '_reminder_thread') and self._reminder_thread:
                self._reminder_thread.quit()
                self._reminder_thread.wait(1000)
        
        if hasattr(self, '_bubble') and self._bubble:
            self._bubble.hide()
        if hasattr(self, '_tray') and self._tray:
            self._tray.hide()
        
        self.close_requested.emit()
        QApplication.quit()
    
    def closeEvent(self, event):
        self._quit()
        event.accept()
    
    def showEvent(self, event):
        super().showEvent(event)
        self._update_bubble_position()
