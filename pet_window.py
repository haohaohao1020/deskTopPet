import sys
import ctypes
import random
import time
import traceback

from PySide6.QtCore import (
    Qt, QTimer, Signal, Slot, QPoint, QRect, 
    QEasingCurve, QSize, QCoreApplication
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPainterPath, QCursor, 
    QAction, QIcon, QPixmap, QGuiApplication
)
from PySide6.QtWidgets import (
    QWidget, QMenu, QSystemTrayIcon, QMessageBox, QApplication
)

from config import ConfigManager
from skins import get_skin, get_skin_info


class PetWindow(QWidget):
    close_requested = Signal()
    
    def __init__(self, app: QApplication):
        print("[DEBUG] PetWindow.__init__ start")
        super().__init__()
        self._app = app
        
        try:
            self._screen = app.primaryScreen().geometry()
            print(f"[DEBUG] Screen geometry: {self._screen}")
            
            self._config = ConfigManager()
            print("[DEBUG] ConfigManager created")
            
            self._dragging = False
            self._drag_offset = QPoint(0, 0)
            self._last_click_time = 0
            self._current_weather = None
            self._frame = 0.0
            self._current_action = "idle"
            self._emotion = "happy"
            self._direction = 1
            self._action_timer = 0
            
            self._setup_window()
            print("[DEBUG] Window setup done")
            
            self._skin = get_skin(self._config.get("pet", "current_skin") or "cat")
            print("[DEBUG] Skin loaded")
            
            self._setup_tray()
            print("[DEBUG] Tray setup done")
            
            self._load_position()
            print("[DEBUG] Position loaded")
            
            self._animation_timer = QTimer(self)
            self._animation_timer.setInterval(50)
            self._animation_timer.timeout.connect(self._on_animation_tick)
            self._animation_timer.start()
            print("[DEBUG] Animation timer started")
            
            print("[DEBUG] PetWindow.__init__ done")
        except Exception as e:
            print(f"[ERROR] __init__: {e}")
            traceback.print_exc()
            raise
    
    def _setup_window(self):
        try:
            flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
            self.setWindowFlags(flags)
            
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setAttribute(Qt.WA_ShowWithoutActivating)
            self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            self.setMouseTracking(True)
            self.setFocusPolicy(Qt.NoFocus)
            
            scale = self._config.get("window", "scale") or 1.0
            width = int(120 * scale)
            height = int(120 * scale)
            self.setFixedSize(width, height)
            self.setWindowOpacity(self._config.get("window", "opacity") or 1.0)
            
            print(f"[DEBUG] Window size: {width}x{height}")
        except Exception as e:
            print(f"[ERROR] _setup_window: {e}")
            traceback.print_exc()
    
    def _setup_tray(self):
        try:
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
            print("[DEBUG] Tray icon shown")
        except Exception as e:
            print(f"[ERROR] _setup_tray: {e}")
            traceback.print_exc()
            self._tray = None
    
    def _load_position(self):
        try:
            x = self._config.get("window", "x") or 500
            y = self._config.get("window", "y") or 300
            self.move(x, y)
            print(f"[DEBUG] Position: {x}, {y}")
        except Exception as e:
            print(f"[ERROR] _load_position: {e}")
    
    @Slot()
    def _on_animation_tick(self):
        try:
            self._frame += 0.05
            self._action_timer += 1
            
            if self._action_timer > 120:
                self._action_timer = 0
                actions = ["idle", "walk", "idle", "idle"]
                new_action = random.choice(actions)
                if new_action != self._current_action:
                    self._current_action = new_action
                    if new_action == "walk":
                        self._direction = random.choice([-1, 1])
            
            if self._current_action == "walk":
                new_x = self.x() + self._direction * 2
                screen_w = QGuiApplication.primaryScreen().geometry().width()
                if new_x < 0 or new_x + self.width() > screen_w:
                    self._direction *= -1
                else:
                    self.move(new_x, self.y())
            
            self.update()
        except Exception as e:
            print(f"[ERROR] _on_animation_tick: {e}")
    
    @Slot(QSystemTrayIcon.ActivationReason)
    def _on_tray_activated(self, reason):
        try:
            if reason == QSystemTrayIcon.DoubleClick:
                if self.isHidden():
                    self.show()
                else:
                    self.raise_()
            elif reason == QSystemTrayIcon.Context:
                self._show_menu(QCursor.pos())
        except Exception as e:
            print(f"[ERROR] _on_tray_activated: {e}")
    
    def paintEvent(self, event):
        try:
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            p.setRenderHint(QPainter.SmoothPixmapTransform)
            
            rect = self.rect()
            self._skin.draw(p, rect, {}, self._emotion, self._current_action, self._frame)
            
            p.end()
        except Exception as e:
            print(f"[ERROR] paintEvent: {e}")
            traceback.print_exc()
    
    def mousePressEvent(self, event):
        try:
            if event.button() == Qt.LeftButton:
                self._dragging = True
                self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                self._current_action = "idle"
                self.raise_()
            elif event.button() == Qt.RightButton:
                self._show_menu(event.globalPosition().toPoint())
        except Exception as e:
            print(f"[ERROR] mousePressEvent: {e}")
    
    def mouseMoveEvent(self, event):
        try:
            if self._dragging:
                np = event.globalPosition().toPoint() - self._drag_offset
                self.move(np)
        except Exception as e:
            print(f"[ERROR] mouseMoveEvent: {e}")
    
    def mouseReleaseEvent(self, event):
        try:
            if event.button() == Qt.LeftButton:
                if self._dragging:
                    self._dragging = False
                    self._action_timer = 0
                    ct = time.time()
                    if ct - self._last_click_time < 0.3:
                        self._last_click_time = 0
                        print("[DEBUG] Double click!")
                    else:
                        self._last_click_time = ct
                        self._emotion = "happy"
                        self.update()
        except Exception as e:
            print(f"[ERROR] mouseReleaseEvent: {e}")
    
    def _show_menu(self, pos):
        try:
            menu = QMenu(self)
            
            sm = menu.addMenu("🎨 更换皮肤")
            si = get_skin_info()
            cs = self._config.get("pet", "current_skin")
            for sid, info in si.items():
                a = QAction(f"{info['emoji']} {info['name']}", self)
                a.setCheckable(True)
                a.setChecked(sid == cs)
                a.setData(sid)
                a.triggered.connect(lambda checked, s=sid: self._switch_skin(s))
                sm.addAction(a)
            
            menu.addSeparator()
            
            qa = QAction("❌ 退出", self)
            qa.triggered.connect(self._quit)
            menu.addAction(qa)
            
            menu.exec(pos)
        except Exception as e:
            print(f"[ERROR] _show_menu: {e}")
            traceback.print_exc()
    
    @Slot(str)
    def _switch_skin(self, sid: str):
        try:
            self._config.set("pet", "current_skin", sid)
            self._skin = get_skin(sid)
            self.update()
            print(f"[DEBUG] Switched to skin: {sid}")
        except Exception as e:
            print(f"[ERROR] _switch_skin: {e}")
    
    @Slot()
    def _quit(self):
        try:
            print("[DEBUG] Quitting...")
            self._config.set("window", "x", self.x())
            self._config.set("window", "y", self.y())
            
            if self._tray:
                self._tray.hide()
            
            self.close_requested.emit()
            QApplication.quit()
        except Exception as e:
            print(f"[ERROR] _quit: {e}")
    
    def closeEvent(self, event):
        print("[DEBUG] closeEvent")
        self._quit()
        event.accept()
