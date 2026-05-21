import math
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QLinearGradient, QRadialGradient, QFont, QFontMetrics
from PySide6.QtCore import QPointF, QRectF, Qt


class BongocatRenderer:
    def __init__(self):
        self._left_paw_offset = 0.0
        self._right_paw_offset = 0.0
        self._left_paw_key = ""
        self._right_paw_key = ""
        self._mouse_action = "none"
        self._mouse_click_progress = 0.0
        self._mouse_scroll_progress = 0.0
        self._mouse_scroll_dir = 0.0
        self._is_idle = True
        self._emotion = "happy"
        self._frame = 0.0
        self._action = "idle"

    def update_left_paw(self, offset: float, progress: float, key_label: str):
        self._left_paw_offset = offset
        self._left_paw_key = key_label

    def update_right_paw(self, offset: float, progress: float, key_label: str):
        self._right_paw_offset = offset
        self._right_paw_key = key_label

    def update_mouse(self, action: str, click_progress: float, scroll_dir: float):
        self._mouse_action = action
        self._mouse_click_progress = click_progress
        if scroll_dir != 0.0:
            self._mouse_scroll_dir = scroll_dir

    def set_emotion(self, emotion: str):
        self._emotion = emotion

    def set_frame(self, frame: float):
        self._frame = frame

    def set_action(self, action: str):
        self._action = action

    def set_idle(self, idle: bool):
        self._is_idle = idle

    def draw(self, painter: QPainter, rect: QRectF):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w = rect.width()
        h = rect.height()

        kb_w = min(w * 0.92, 260.0)
        kb_h = min(h * 0.38, 90.0)
        kb_x = rect.center().x() - kb_w / 2
        kb_y = rect.bottom() - kb_h - 8

        kb_layout = self._compute_keyboard_layout(kb_x, kb_y, kb_w, kb_h)

        self._draw_keyboard(painter, kb_layout, kb_x, kb_y, kb_w, kb_h)

        mouse_w = kb_w * 0.16
        mouse_h = kb_h * 0.65
        mouse_x = kb_x + kb_w + 6
        mouse_y = kb_y + kb_h - mouse_h
        self._draw_mouse(painter, mouse_x, mouse_y, mouse_w, mouse_h)

        self._draw_cat(painter, rect, kb_x, kb_y, kb_w, kb_h, kb_layout)

        painter.restore()

    def _compute_keyboard_layout(self, kb_x, kb_y, kb_w, kb_h):
        rows = 4
        key_gap = 2.0
        usable_w = kb_w - key_gap * 2

        row_widths = [10, 10, 10, 10]
        key_w = usable_w / 10.0

        key_h = (kb_h - key_gap * (rows + 1)) / rows

        layout = {}
        row_keys = [
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'ENT'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', '.', 'BSP'],
            ['CTL', 'SFT', 'ALT', 'SPC1', 'SPC2', 'SPC3', 'SPC4', 'ALT', 'SFT', 'CTL'],
        ]

        for row_idx in range(rows):
            for col_idx in range(10):
                label = row_keys[row_idx][col_idx]
                x = kb_x + key_gap + col_idx * (key_w + key_gap * 0.5)
                y = kb_y + key_gap + row_idx * (key_h + key_gap * 0.5)
                layout[label] = QRectF(x, y, key_w, key_h)

        layout['SPC'] = QRectF(
            kb_x + key_gap * 2 + 3 * (key_w + key_gap * 0.5),
            kb_y + key_gap + 3 * (key_h + key_gap * 0.5),
            4 * key_w + 3 * key_gap * 0.5,
            key_h
        )

        special_positions = {
            'Key.q': 'Q', 'Key.w': 'W', 'Key.e': 'E', 'Key.r': 'R', 'Key.t': 'T',
            'Key.y': 'Y', 'Key.u': 'U', 'Key.i': 'I', 'Key.o': 'O', 'Key.p': 'P',
            'Key.a': 'A', 'Key.s': 'S', 'Key.d': 'D', 'Key.f': 'F', 'Key.g': 'G',
            'Key.h': 'H', 'Key.j': 'J', 'Key.k': 'K', 'Key.l': 'L',
            'Key.z': 'Z', 'Key.x': 'X', 'Key.c': 'C', 'Key.v': 'V',
            'Key.b': 'B', 'Key.n': 'N', 'Key.m': 'M',
            'Key.enter': 'ENT', 'Key.backspace': 'BSP',
            'Key.space': 'SPC',
            'Key.shift_l': 'SFT', 'Key.shift_r': 'SFT',
            'Key.ctrl_l': 'CTL', 'Key.ctrl_r': 'CTL',
            'Key.alt_l': 'ALT', 'Key.alt_r': 'ALT',
        }

        self._key_map = special_positions
        self._kb_layout = layout
        self._kb_key_rect = QRectF(kb_x, kb_y, kb_w, kb_h)
        return layout

    def _draw_keyboard(self, painter, layout, kb_x, kb_y, kb_w, kb_h):
        base_color = QColor(50, 55, 65)
        border_color = QColor(30, 33, 42)

        painter.setBrush(QBrush(QColor(40, 44, 52)))
        painter.setPen(QPen(border_color, 2))
        painter.drawRoundedRect(QRectF(kb_x - 3, kb_y - 3, kb_w + 6, kb_h + 6), 6, 6)

        for label, key_rect in layout.items():
            is_pressed = False
            if self._left_paw_key and self._match_key(self._left_paw_key, label):
                is_pressed = True
            if self._right_paw_key and self._match_key(self._right_paw_key, label):
                is_pressed = True

            if is_pressed:
                self._draw_key(painter, key_rect, label, True)
            else:
                self._draw_key(painter, key_rect, label, False)

    def _match_key(self, paw_key, layout_label):
        key_map = {
            'SPC': ['Key.space', 'SPC'],
            'ENT': ['Key.enter', 'ENT'],
            'BSP': ['Key.backspace', 'BSP'],
            'SFT': ['Key.shift_l', 'Key.shift_r', 'Key.shift', 'SFT'],
            'CTL': ['Key.ctrl_l', 'Key.ctrl_r', 'Key.ctrl', 'CTL'],
            'ALT': ['Key.alt_l', 'Key.alt_r', 'Key.alt', 'ALT'],
        }
        if layout_label in key_map:
            return paw_key in key_map[layout_label]
        if len(paw_key) == 5 and paw_key.startswith('Key.'):
            ch = paw_key.split('.')[-1].upper()
            return ch == layout_label
        return paw_key.upper() == layout_label

    def _draw_key(self, painter, rect, label, is_pressed):
        if is_pressed:
            base = QColor(255, 180, 80)
            gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            gradient.setColorAt(0, base.lighter(130))
            gradient.setColorAt(0.5, base)
            gradient.setColorAt(1, base.darker(120))
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(220, 140, 40), 1))

            glow = QRadialGradient(rect.center(), max(rect.width(), rect.height()))
            glow.setColorAt(0, QColor(255, 200, 100, 80))
            glow.setColorAt(1, QColor(255, 200, 100, 0))
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.NoPen)
            glow_rect = QRectF(
                rect.x() - 4, rect.y() - 4,
                rect.width() + 8, rect.height() + 8
            )
            painter.drawRoundedRect(glow_rect, 6, 6)

            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(220, 140, 40), 1))
        else:
            base = QColor(70, 75, 85)
            gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            gradient.setColorAt(0, base.lighter(120))
            gradient.setColorAt(0.5, base)
            gradient.setColorAt(1, base.darker(115))
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(45, 48, 58), 1))

        painter.drawRoundedRect(rect, 3, 3)

        painter.setPen(QPen(QColor(200, 205, 215) if not is_pressed else QColor(60, 40, 10), 1))
        font = QFont("Arial", 7 if len(label) > 2 else 8)
        font.setBold(not is_pressed)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, label)

    def _draw_mouse(self, painter, x, y, w, h):
        body_color = QColor(55, 60, 70)
        border_color = QColor(35, 38, 48)

        gradient = QLinearGradient(x, y, x, y + h)
        gradient.setColorAt(0, body_color.lighter(125))
        gradient.setColorAt(1, body_color.darker(115))

        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(QRectF(x, y, w, h), w * 0.4, h * 0.25)

        button_color = QColor(100, 105, 115)
        click_offset = 0.0
        is_clicked = self._mouse_action in ('left_click', 'right_click')
        is_left = self._mouse_action == 'left_click'
        is_right = self._mouse_action == 'right_click'

        if is_left and self._mouse_click_progress < 0.5:
            click_offset = 1.0

        left_btn = QRectF(x + 2, y + 3, (w - 5) / 2, h * 0.45)
        painter.setBrush(QBrush(button_color.darker(115) if not is_left else QColor(255, 160, 60)))
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(left_btn.translated(0, click_offset if is_left else 0), 3, 2)

        if is_right and self._mouse_click_progress < 0.5:
            click_offset = 1.0

        right_btn = QRectF(x + w / 2 + 1, y + 3, (w - 5) / 2, h * 0.45)
        painter.setBrush(QBrush(button_color.darker(115) if not is_right else QColor(255, 160, 60)))
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(right_btn.translated(0, click_offset if is_right else 0), 3, 2)

        wheel_rect = QRectF(x + w * 0.4, y + h * 0.5, w * 0.2, h * 0.18)
        if self._mouse_action in ('scroll_up', 'scroll_down'):
            painter.setBrush(QBrush(QColor(255, 180, 80)))
        else:
            painter.setBrush(QBrush(QColor(90, 95, 105)))
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(wheel_rect, 2, 2)

        if self._mouse_action in ('scroll_up', 'scroll_down'):
            dy = 0.0
            if self._mouse_action == 'scroll_up':
                dy = -3.0 * (1.0 - self._mouse_scroll_progress)
            else:
                dy = 3.0 * (1.0 - self._mouse_scroll_progress)
            painter.setBrush(QBrush(QColor(255, 200, 100)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(wheel_rect.translated(0, dy), 2, 2)

    def _draw_cat(self, painter, rect, kb_x, kb_y, kb_w, kb_h, kb_layout):
        cx = rect.center().x()
        cy = kb_y - 10

        cat_w = kb_w * 0.85
        cat_h = (kb_y - rect.top() + 15) * 0.85

        cat_left = cx - cat_w / 2
        cat_top = rect.top() + 5
        cat_rect = QRectF(cat_left, cat_top, cat_w, cat_h)

        body_color = QColor(255, 200, 150)
        ear_color = QColor(230, 180, 130)
        eye_color = QColor(80, 80, 120)

        if self._emotion == "angry":
            body_color = QColor(255, 160, 160)
            ear_color = QColor(220, 120, 120)
            eye_color = QColor(255, 80, 80)
        elif self._emotion == "sleepy":
            body_color = QColor(210, 190, 220)
            ear_color = QColor(190, 170, 200)
        elif self._emotion == "shy":
            body_color = QColor(255, 210, 220)
            ear_color = QColor(235, 190, 205)

        gradient = QRadialGradient(cat_rect.center(), max(cat_w, cat_h) * 0.6)
        gradient.setColorAt(0, body_color.lighter(125))
        gradient.setColorAt(0.6, body_color)
        gradient.setColorAt(1, body_color.darker(115))

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)

        head_rect = QRectF(
            cat_rect.center().x() - cat_w * 0.38,
            cat_rect.top() + 2,
            cat_w * 0.76,
            cat_h * 0.62
        )

        body_rect = QRectF(
            cat_rect.center().x() - cat_w * 0.45,
            cat_rect.top() + cat_h * 0.48,
            cat_w * 0.9,
            cat_h * 0.50
        )

        painter.drawRoundedRect(body_rect, 18, 18)
        painter.drawRoundedRect(head_rect, 22, 22)

        self._draw_ears(painter, head_rect, ear_color)
        self._draw_eyes(painter, head_rect, eye_color)
        self._draw_nose_mouth(painter, head_rect)
        self._draw_whiskers(painter, head_rect)
        self._draw_tail(painter, body_rect, body_color)
        self._draw_paws(painter, cat_rect, kb_layout, kb_x, kb_y, kb_w, kb_h, body_color)

        if self._emotion in ("happy", "shy"):
            self._draw_blush(painter, head_rect)

    def _draw_ears(self, painter, head_rect, color):
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(150), 1))

        left_ear = QPointF(head_rect.left() + head_rect.width() * 0.18, head_rect.top() + 2)
        right_ear = QPointF(head_rect.right() - head_rect.width() * 0.18, head_rect.top() + 2)

        for ex, ey in [(left_ear.x(), left_ear.y()), (right_ear.x(), right_ear.y())]:
            path = QPainterPath()
            path.moveTo(ex - 10, ey + 8)
            path.lineTo(ex, ey - 18)
            path.lineTo(ex + 10, ey + 8)
            path.closeSubpath()
            painter.drawPath(path)

            painter.setBrush(QBrush(color.lighter(135)))
            inner = QPainterPath()
            inner.moveTo(ex - 6, ey + 8)
            inner.lineTo(ex, ey - 10)
            inner.lineTo(ex + 6, ey + 8)
            inner.closeSubpath()
            painter.drawPath(inner)
            painter.setBrush(QBrush(color))

    def _draw_eyes(self, painter, head_rect, color):
        left = QPointF(head_rect.center().x() - head_rect.width() * 0.2, head_rect.top() + head_rect.height() * 0.38)
        right = QPointF(head_rect.center().x() + head_rect.width() * 0.2, head_rect.top() + head_rect.height() * 0.38)

        blink = (self._frame * 1.8) % 1.0 < 0.12
        eye_h = 3 if blink or self._emotion == "sleepy" else 12

        if self._emotion == "sleepy":
            painter.setPen(QPen(color, 2))
            painter.setBrush(Qt.NoBrush)
            for c in [left, right]:
                painter.drawArc(QRectF(c.x() - 8, c.y() - 3, 16, 8), 0, 180 * 16)
            return

        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(color.darker(170), 1))
        for c in [left, right]:
            painter.drawEllipse(QRectF(c.x() - 7, c.y() - eye_h / 2, 14, eye_h))

        if not blink:
            painter.setBrush(QBrush(color))
            px = 3 * (1 if (self._frame % 1.0) > 0.5 else -1) if self._action in ("walk", "run") else 0
            for c in [left, right]:
                painter.drawEllipse(QRectF(c.x() - 4 + px, c.y() - 4, 8, 8))
                painter.setBrush(QBrush(QColor(255, 255, 255)))
                painter.drawEllipse(QRectF(c.x() - 2 + px, c.y() - 3, 3, 3))
                painter.setBrush(QBrush(color))

    def _draw_nose_mouth(self, painter, head_rect):
        nc = QPointF(head_rect.center().x(), head_rect.top() + head_rect.height() * 0.52)

        nose_color = QColor(200, 150, 150)
        painter.setBrush(QBrush(nose_color))
        painter.setPen(Qt.NoPen)

        path = QPainterPath()
        path.moveTo(nc.x() - 4, nc.y())
        path.lineTo(nc.x(), nc.y() + 5)
        path.lineTo(nc.x() + 4, nc.y())
        path.arcTo(nc.x() - 4, nc.y() - 4, 8, 8, 0, -180)
        painter.drawPath(path)

        painter.setPen(QPen(nose_color.darker(150), 1.5))
        painter.setBrush(Qt.NoBrush)

        if self._emotion == "happy":
            painter.drawArc(QRectF(nc.x() - 8, nc.y() + 2, 16, 10), 180 * 16, 180 * 16)
        elif self._emotion == "angry":
            painter.drawArc(QRectF(nc.x() - 8, nc.y() + 6, 16, 8), 0, 180 * 16)
        elif self._emotion == "sleepy":
            painter.drawLine(nc.x() - 5, nc.y() + 6, nc.x() + 5, nc.y() + 6)
        else:
            painter.drawArc(QRectF(nc.x() - 6, nc.y() + 3, 12, 8), 180 * 16, 120 * 16)

    def _draw_whiskers(self, painter, head_rect):
        painter.setPen(QPen(QColor(160, 140, 110), 1))
        for side in [-1, 1]:
            sx = head_rect.center().x() + side * head_rect.width() * 0.15
            for i, a in enumerate([-18, 0, 18]):
                y = head_rect.top() + head_rect.height() * 0.48 + i * 4
                painter.drawLine(QPointF(sx, y), QPointF(sx + side * 18, y + a * 0.2))

    def _draw_tail(self, painter, body_rect, color):
        ts = QPointF(body_rect.right() - 5, body_rect.bottom() - 12)
        swing = self._frame * (5 if self._emotion == "happy" else 2.5)
        swing = 12 * math.sin(swing)

        painter.setPen(QPen(color, 6, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)

        path = QPainterPath()
        path.moveTo(ts)
        path.quadTo(ts.x() + 14, ts.y() - 14, ts.x() + 28, ts.y() - 10 + swing)
        painter.drawPath(path)

        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(ts.x() + 24, ts.y() - 14 + swing, 8, 8))

    def _draw_paws(self, painter, cat_rect, kb_layout, kb_x, kb_y, kb_w, kb_h, body_color):
        paw_color = body_color.darker(112)
        paw_w = 22
        paw_h = 14

        kb_center_y = kb_y + kb_h * 0.5

        left_paw_x = kb_x + kb_w * 0.25
        right_paw_x = kb_x + kb_w * 0.75
        base_y = kb_y + 3

        left_target = self._get_paw_target('left', kb_layout, kb_x, kb_y)
        right_target = self._get_paw_target('right', kb_layout, kb_x, kb_y)

        if self._left_paw_key and left_target:
            target_key_rect = left_target
            target_x = target_key_rect.center().x()
            target_y = target_key_rect.center().y()
            self._draw_animated_paw(painter, cat_rect, target_x, target_y,
                                    self._left_paw_offset, paw_color, paw_w, paw_h, True)
        else:
            self._draw_resting_paw(painter, left_paw_x, base_y, paw_w, paw_h, paw_color, True)

        if self._right_paw_key and right_target:
            target_key_rect = right_target
            target_x = target_key_rect.center().x()
            target_y = target_key_rect.center().y()
            self._draw_animated_paw(painter, cat_rect, target_x, target_y,
                                    self._right_paw_offset, paw_color, paw_w, paw_h, False)
        else:
            self._draw_resting_paw(painter, right_paw_x, base_y, paw_w, paw_h, paw_color, False)

    def _get_paw_target(self, side, kb_layout, kb_x, kb_y):
        key = self._left_paw_key if side == 'left' else self._right_paw_key
        if not key:
            return None

        if key in self._key_map:
            label = self._key_map[key]
            if label in kb_layout:
                return kb_layout[label]
        elif len(key) == 5 and key.startswith('Key.'):
            ch = key.split('.')[-1].upper()
            if ch in kb_layout:
                return kb_layout[ch]

        for lbl, rect in kb_layout.items():
            if lbl == key.upper():
                return rect

        return None

    def _draw_animated_paw(self, painter, cat_rect, target_x, target_y,
                           offset, color, paw_w, paw_h, is_left):
        shoulder_y = cat_rect.bottom() - 5

        if is_left:
            shoulder_x = cat_rect.left() + cat_rect.width() * 0.25
        else:
            shoulder_x = cat_rect.right() - cat_rect.width() * 0.25

        lift_amount = max(0, offset)
        press_amount = max(0, -offset)

        paw_y = target_y - lift_amount + press_amount
        paw_x = target_x

        paw_color = color
        if lift_amount > 2:
            paw_color = color.lighter(110)
        elif press_amount > 2:
            paw_color = color.darker(115)

        painter.setPen(QPen(color.darker(130), 3, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)

        arm_path = QPainterPath()
        arm_path.moveTo(shoulder_x, shoulder_y)
        ctrl_x = (shoulder_x + paw_x) / 2
        ctrl_y = (shoulder_y + paw_y) / 2 - 15 - lift_amount * 0.3
        arm_path.quadTo(ctrl_x, ctrl_y, paw_x, paw_y)
        painter.drawPath(arm_path)

        painter.setBrush(QBrush(paw_color))
        painter.setPen(QPen(paw_color.darker(140), 1))

        paw_rect = QRectF(paw_x - paw_w / 2, paw_y - paw_h / 2, paw_w, paw_h)
        painter.drawRoundedRect(paw_rect, paw_h * 0.5, paw_h * 0.5)

        if press_amount > 1:
            shadow = QRadialGradient(QPointF(paw_x, target_y + paw_h * 0.8), 12)
            shadow.setColorAt(0, QColor(255, 200, 100, 100))
            shadow.setColorAt(1, QColor(255, 200, 100, 0))
            painter.setBrush(QBrush(shadow))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QRectF(paw_x - 10, target_y + 2, 20, 8))

    def _draw_resting_paw(self, painter, x, y, paw_w, paw_h, color, is_left):
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(140), 1))
        painter.drawRoundedRect(QRectF(x - paw_w / 2, y, paw_w, paw_h), paw_h * 0.5, paw_h * 0.5)

    def _draw_blush(self, painter, head_rect):
        alpha = 110 if self._emotion == "happy" else 140
        painter.setBrush(QBrush(QColor(255, 150, 150, alpha)))
        painter.setPen(Qt.NoPen)
        bw = head_rect.width() * 0.15
        bh = head_rect.height() * 0.10
        painter.drawEllipse(QRectF(
            head_rect.left() + head_rect.width() * 0.08,
            head_rect.top() + head_rect.height() * 0.42,
            bw, bh
        ))
        painter.drawEllipse(QRectF(
            head_rect.right() - head_rect.width() * 0.08 - bw,
            head_rect.top() + head_rect.height() * 0.42,
            bw, bh
        ))
