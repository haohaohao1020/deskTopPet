import ctypes
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QPoint, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QFont, QLinearGradient, QAction
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QDialog, QLineEdit, QTimeEdit, QCheckBox, QListWidget,
    QListWidgetItem, QSlider, QGroupBox, QFormLayout, QMessageBox
)


class SpeechBubble(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)
        
        self._text = ""
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timeout)
        
        self._opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self._opacity_anim.setDuration(300)
        self._opacity_anim.setEasingCurve(QEasingCurve.InOutQuad)
        
        self._hidden = True
        self.hide()
    
    def show_message(self, text: str, duration: int = 3000):
        if not text:
            return
        self._text = text
        self._update_size()
        if self._hidden:
            self._opacity_anim.setStartValue(0.0)
            self._opacity_anim.setEndValue(1.0)
            self.show()
            self._opacity_anim.start()
            self._hidden = False
        self._timer.start(duration)
    
    def _update_size(self):
        from PySide6.QtGui import QFontMetrics
        font = QFont("Microsoft YaHei", 10)
        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(self._text)
        th = fm.height()
        self.setFixedSize(max(tw + 32, 90), th + 42)
    
    @Slot()
    def _on_timeout(self):
        self._opacity_anim.setStartValue(1.0)
        self._opacity_anim.setEndValue(0.0)
        self._opacity_anim.finished.connect(self._on_fade_done)
        self._opacity_anim.start()
    
    @Slot()
    def _on_fade_done(self):
        self.hide()
        self._hidden = True
        try:
            self._opacity_anim.finished.disconnect(self._on_fade_done)
        except Exception:
            pass
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect().adjusted(0, 0, 0, -14)
        ap = QPoint(self.width() // 2, self.height() - 2)
        al = QPoint(self.width() // 2 - 11, self.height() - 16)
        ar = QPoint(self.width() // 2 + 11, self.height() - 16)
        
        bp = QPainterPath()
        bp.addRoundedRect(rect, 10, 10)
        
        apath = QPainterPath()
        apath.moveTo(al)
        apath.lineTo(ap)
        apath.lineTo(ar)
        apath.closeSubpath()
        
        fp = QPainterPath()
        fp.addPath(bp)
        fp.addPath(apath)
        
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0, QColor(255, 255, 255, 245))
        g.setColorAt(1, QColor(240, 245, 255, 245))
        
        painter.setBrush(QBrush(g))
        painter.setPen(QPen(QColor(180, 200, 220), 1))
        painter.drawPath(fp)
        
        painter.setPen(QPen(QColor(60, 60, 80)))
        painter.setFont(QFont("Microsoft YaHei", 10))
        painter.drawText(rect.adjusted(15, 10, -15, -10), Qt.AlignCenter, self._text)


class ReminderDialog(QDialog):
    reminders_updated = Signal(list)
    
    def __init__(self, current_reminders=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("定时提醒设置")
        self.setMinimumSize(500, 400)
        self._reminders = current_reminders.copy() if current_reminders else []
        
        layout = QVBoxLayout(self)
        
        lg = QGroupBox("已设置提醒")
        ll = QVBoxLayout(lg)
        self._list = QListWidget()
        ll.addWidget(self._list)
        
        bl = QHBoxLayout()
        self._add_btn = QPushButton("添加")
        self._edit_btn = QPushButton("编辑")
        self._del_btn = QPushButton("删除")
        bl.addWidget(self._add_btn)
        bl.addWidget(self._edit_btn)
        bl.addWidget(self._del_btn)
        ll.addLayout(bl)
        layout.addWidget(lg)
        
        fg = QGroupBox("添加/编辑提醒")
        fl = QFormLayout(fg)
        
        self._title = QLineEdit()
        self._title.setPlaceholderText("例如：喝水提醒")
        fl.addRow("标题:", self._title)
        
        self._msg = QLineEdit()
        self._msg.setPlaceholderText("例如：该喝水了！")
        fl.addRow("消息:", self._msg)
        
        self._time = QTimeEdit()
        self._time.setDisplayFormat("HH:mm")
        fl.addRow("时间:", self._time)
        
        dl = QHBoxLayout()
        self._day_cb = []
        for n in ["一", "二", "三", "四", "五", "六", "日"]:
            cb = QCheckBox(f"周{n}")
            cb.setChecked(True)
            self._day_cb.append(cb)
            dl.addWidget(cb)
        fl.addRow("重复:", dl)
        
        save = QPushButton("保存修改")
        fl.addRow(save)
        layout.addWidget(fg)
        
        bbl = QHBoxLayout()
        ok = QPushButton("确定")
        cancel = QPushButton("取消")
        bbl.addStretch()
        bbl.addWidget(ok)
        bbl.addWidget(cancel)
        layout.addLayout(bbl)
        
        self._add_btn.clicked.connect(self._on_add)
        self._edit_btn.clicked.connect(self._on_load)
        self._del_btn.clicked.connect(self._on_del)
        save.clicked.connect(self._on_save)
        ok.clicked.connect(self._on_ok)
        cancel.clicked.connect(self.reject)
        
        self._refresh()
        self._editing = -1
    
    def _refresh(self):
        self._list.clear()
        dn = ["一", "二", "三", "四", "五", "六", "日"]
        for r in self._reminders:
            d = r.get('days', list(range(7)))
            ds = "每天" if len(d) == 7 else ",".join([dn[x] for x in d])
            t = r.get('time', '')
            ti = r.get('title', '')
            self._list.addItem(QListWidgetItem(f"{t} [周{ds}] - {ti}"))
    
    @Slot()
    def _on_add(self):
        self._editing = -1
        self._title.clear()
        self._msg.clear()
        for cb in self._day_cb:
            cb.setChecked(True)
    
    @Slot()
    def _on_load(self):
        from PySide6.QtCore import QTime
        idx = self._list.currentRow()
        if 0 <= idx < len(self._reminders):
            self._editing = idx
            r = self._reminders[idx]
            self._title.setText(r.get('title', ''))
            self._msg.setText(r.get('message', ''))
            h, m = map(int, r.get('time', '08:00').split(':'))
            self._time.setTime(QTime(h, m))
            days = r.get('days', list(range(7)))
            for i, cb in enumerate(self._day_cb):
                cb.setChecked(i in days)
    
    @Slot()
    def _on_del(self):
        idx = self._list.currentRow()
        if 0 <= idx < len(self._reminders):
            del self._reminders[idx]
            self._refresh()
    
    @Slot()
    def _on_save(self):
        t = self._title.text().strip()
        if not t:
            QMessageBox.warning(self, "提示", "请输入标题！")
            return
        days = [i for i, cb in enumerate(self._day_cb) if cb.isChecked()]
        if not days:
            QMessageBox.warning(self, "提示", "请至少选择一天！")
            return
        nr = {'title': t, 'message': self._msg.text().strip(),
              'time': self._time.time().toString("HH:mm"), 'days': days}
        if self._editing >= 0:
            self._reminders[self._editing] = nr
        else:
            self._reminders.append(nr)
        self._refresh()
        self._title.clear()
        self._editing = -1
    
    @Slot()
    def _on_ok(self):
        self.reminders_updated.emit(self._reminders)
        self.accept()


class SettingsDialog(QDialog):
    settings_changed = Signal(dict)
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self._config = config_manager
        self.setWindowTitle("宠物设置")
        self.setMinimumSize(420, 380)
        
        layout = QVBoxLayout(self)
        
        wg = QGroupBox("窗口设置")
        wl = QFormLayout(wg)
        
        self._scale = QSlider(Qt.Horizontal)
        self._scale.setRange(50, 200)
        self._scale.setValue(int(self._config.get("window", "scale") * 100))
        self._scale_label = QLabel(f"{self._scale.value()}%")
        sl = QHBoxLayout()
        sl.addWidget(self._scale)
        sl.addWidget(self._scale_label)
        wl.addRow("缩放比例:", sl)
        
        self._opacity = QSlider(Qt.Horizontal)
        self._opacity.setRange(30, 100)
        self._opacity.setValue(int(self._config.get("window", "opacity") * 100))
        self._opacity_label = QLabel(f"{self._opacity.value()}%")
        ol = QHBoxLayout()
        ol.addWidget(self._opacity)
        ol.addWidget(self._opacity_label)
        wl.addRow("透明度:", ol)
        layout.addWidget(wg)
        
        self._scale.valueChanged.connect(lambda v: self._scale_label.setText(f"{v}%"))
        self._opacity.valueChanged.connect(lambda v: self._opacity_label.setText(f"{v}%"))
        
        pg = QGroupBox("宠物行为")
        pl = QFormLayout(pg)
        
        self._auto_sleep = QCheckBox("闲置自动睡眠")
        self._auto_sleep.setChecked(self._config.get("pet", "auto_sleep"))
        pl.addRow(self._auto_sleep)
        
        self._edge_snap = QCheckBox("边缘吸附")
        self._edge_snap.setChecked(self._config.get("window", "edge_snap"))
        pl.addRow(self._edge_snap)
        
        self._always_top = QCheckBox("窗口置顶")
        self._always_top.setChecked(self._config.get("window", "always_on_top"))
        pl.addRow(self._always_top)
        
        self._click_through = QCheckBox("鼠标穿透(可能影响交互)")
        self._click_through.setChecked(self._config.get("window", "click_through"))
        pl.addRow(self._click_through)
        layout.addWidget(pg)
        
        bbl = QHBoxLayout()
        ok = QPushButton("确定")
        cancel = QPushButton("取消")
        bbl.addStretch()
        bbl.addWidget(ok)
        bbl.addWidget(cancel)
        layout.addLayout(bbl)
        
        ok.clicked.connect(self._on_ok)
        cancel.clicked.connect(self.reject)
    
    @Slot()
    def _on_ok(self):
        s = {
            "window": {
                "scale": self._scale.value() / 100.0,
                "opacity": self._opacity.value() / 100.0,
                "edge_snap": self._edge_snap.isChecked(),
                "always_on_top": self._always_top.isChecked(),
                "click_through": self._click_through.isChecked()
            },
            "pet": {"auto_sleep": self._auto_sleep.isChecked()}
        }
        self.settings_changed.emit(s)
        self.accept()
