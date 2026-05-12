import math
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QLinearGradient, QRadialGradient
from PySide6.QtCore import QPointF, QRectF, Qt

class SkinBase:
    def __init__(self):
        self.scale = 1.0
    
    def draw(self, painter: QPainter, rect: QRectF, state: dict, emotion: str, action: str, frame: float):
        raise NotImplementedError


class CatSkin(SkinBase):
    def draw(self, painter: QPainter, rect: QRectF, state: dict, emotion: str, action: str, frame: float):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        
        cx = rect.center().x()
        cy = rect.center().y() + 8
        
        body_y_offset = 0
        if action == "jump":
            t = (frame % 1.0)
            body_y_offset = -25 * math.sin(t * math.pi)
        elif action == "dragged":
            body_y_offset = -12
        
        body_rect = QRectF(cx - 38, cy - 22 + body_y_offset, 76, 58)
        head_rect = QRectF(cx - 32, cy - 52 + body_y_offset, 64, 52)
        
        body_color = QColor(255, 200, 150)
        ear_color = QColor(230, 180, 130)
        eye_color = QColor(80, 80, 120)
        nose_color = QColor(200, 150, 150)
        
        if emotion == "angry":
            body_color = QColor(255, 160, 160)
            ear_color = QColor(220, 120, 120)
            eye_color = QColor(255, 80, 80)
            nose_color = QColor(200, 80, 80)
        elif emotion == "sleepy":
            body_color = QColor(210, 190, 220)
            ear_color = QColor(190, 170, 200)
            eye_color = QColor(150, 150, 180)
        elif emotion == "shy":
            body_color = QColor(255, 210, 220)
            ear_color = QColor(235, 190, 205)
            eye_color = QColor(180, 100, 150)
        
        gradient = QRadialGradient(body_rect.center(), 45)
        gradient.setColorAt(0, body_color.lighter(125))
        gradient.setColorAt(0.6, body_color)
        gradient.setColorAt(1, body_color.darker(115))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(body_rect, 20, 20)
        painter.drawRoundedRect(head_rect, 24, 24)
        
        self._draw_ears(painter, head_rect, ear_color, emotion, frame)
        self._draw_eyes(painter, head_rect, eye_color, emotion, action, frame)
        self._draw_nose_mouth(painter, head_rect, nose_color, emotion, frame)
        self._draw_whiskers(painter, head_rect)
        self._draw_tail(painter, body_rect, body_color, action, frame)
        self._draw_paws(painter, body_rect, body_color.darker(110), action, frame)
        
        if emotion == "happy" or emotion == "shy":
            self._draw_blush(painter, head_rect, emotion)
        
        painter.restore()
    
    def _draw_ears(self, painter, head_rect, color, emotion, frame):
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(150), 1))
        
        left_rot, right_rot = 0, 0
        if emotion == "angry":
            left_rot, right_rot = 22, -22
        elif emotion == "shy":
            left_rot, right_rot = -8, 8
        
        for i, rot in enumerate([-32 + left_rot, 32 + right_rot]):
            painter.save()
            ex = head_rect.left() + 14 if i == 0 else head_rect.right() - 14
            ey = head_rect.top() + 6
            painter.translate(ex, ey)
            painter.rotate(rot)
            
            path = QPainterPath()
            path.moveTo(-13, 0)
            path.lineTo(0, -28)
            path.lineTo(13, 0)
            path.closeSubpath()
            painter.drawPath(path)
            
            painter.setBrush(QBrush(color.lighter(135)))
            inner = QPainterPath()
            inner.moveTo(-8, 0)
            inner.lineTo(0, -20)
            inner.lineTo(8, 0)
            inner.closeSubpath()
            painter.drawPath(inner)
            painter.restore()
    
    def _draw_eyes(self, painter, head_rect, color, emotion, action, frame):
        left = QPointF(head_rect.left() + 22, head_rect.top() + 26)
        right = QPointF(head_rect.right() - 22, head_rect.top() + 26)
        
        blink = (frame * 1.8) % 1.0 < 0.12
        eye_h = 3 if blink or emotion == "sleepy" else 14
        
        if emotion == "sleepy":
            painter.setPen(QPen(color, 2))
            painter.setBrush(Qt.NoBrush)
            for c in [left, right]:
                painter.drawArc(QRectF(c.x() - 9, c.y() - 4, 18, 10), 0, 180 * 16)
            return
        
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(color.darker(170), 1))
        for c in [left, right]:
            painter.drawEllipse(QRectF(c.x() - 7, c.y() - eye_h/2, 14, eye_h))
        
        if not blink:
            painter.setBrush(QBrush(color))
            px = 4 * (1 if (frame % 1.0) > 0.5 else -1) if action == "walk" else 0
            for c in [left, right]:
                painter.drawEllipse(QRectF(c.x() - 4 + px, c.y() - 4, 8, 8))
                painter.setBrush(QBrush(QColor(255, 255, 255)))
                painter.drawEllipse(QRectF(c.x() - 2 + px, c.y() - 3, 3, 3))
                painter.setBrush(QBrush(color))
    
    def _draw_nose_mouth(self, painter, head_rect, nose_color, emotion, frame):
        nc = QPointF(head_rect.center().x(), head_rect.top() + 36)
        
        painter.setBrush(QBrush(nose_color))
        painter.setPen(Qt.NoPen)
        
        path = QPainterPath()
        path.moveTo(nc.x() - 5, nc.y())
        path.lineTo(nc.x(), nc.y() + 6)
        path.lineTo(nc.x() + 5, nc.y())
        path.arcTo(nc.x() - 5, nc.y() - 5, 10, 10, 0, -180)
        painter.drawPath(path)
        
        painter.setPen(QPen(nose_color.darker(150), 1.5))
        painter.setBrush(Qt.NoBrush)
        
        if emotion == "happy":
            painter.drawArc(QRectF(nc.x() - 10, nc.y() + 2, 20, 14), 180 * 16, 180 * 16)
        elif emotion == "angry":
            painter.drawArc(QRectF(nc.x() - 10, nc.y() + 9, 20, 10), 0, 180 * 16)
        elif emotion == "sleepy":
            painter.drawLine(nc.x() - 6, nc.y() + 7, nc.x() + 6, nc.y() + 7)
        else:
            painter.drawArc(QRectF(nc.x() - 8, nc.y() + 5, 16, 10), 180 * 16, 120 * 16)
    
    def _draw_whiskers(self, painter, head_rect):
        painter.setPen(QPen(QColor(160, 140, 110), 1))
        for side in [-1, 1]:
            sx = head_rect.center().x() + side * 16
            for i, a in enumerate([-22, 0, 22]):
                y = head_rect.top() + 30 + i * 5
                painter.drawLine(QPointF(sx, y), QPointF(sx + side * 22, y + a * 0.25))
    
    def _draw_tail(self, painter, body_rect, color, action, frame):
        ts = QPointF(body_rect.right() - 6, body_rect.bottom() - 16)
        swing = frame * (5 if action == "happy" else 2.5)
        swing = 15 * math.sin(swing)
        
        painter.setPen(QPen(color, 7, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)
        
        path = QPainterPath()
        path.moveTo(ts)
        path.quadTo(ts.x() + 18, ts.y() - 18, ts.x() + 35, ts.y() - 12 + swing)
        painter.drawPath(path)
        
        painter.setBrush(QBrush(color))
        painter.drawEllipse(QRectF(ts.x() + 30, ts.y() - 18 + swing, 11, 11))
    
    def _draw_paws(self, painter, body_rect, color, action, frame):
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        
        t = frame % 1.0
        off = [0, 0]
        if action in ["walk", "run"]:
            s = 7 if action == "run" else 4
            off = [-s * (1 if t < 0.5 else 0), -s * (1 if t >= 0.5 else 0)]
        
        for i, o in enumerate(off):
            x = body_rect.left() + 12 + i * 38
            y = body_rect.bottom() - 8 + o
            painter.drawEllipse(QRectF(x, y, 20, 11))
    
    def _draw_blush(self, painter, head_rect, emotion):
        alpha = 110 if emotion == "happy" else 140
        painter.setBrush(QBrush(QColor(255, 150, 150, alpha)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(head_rect.left() + 7, head_rect.top() + 30, 15, 10))
        painter.drawEllipse(QRectF(head_rect.right() - 22, head_rect.top() + 30, 15, 10))


class DogSkin(SkinBase):
    def draw(self, painter: QPainter, rect: QRectF, state: dict, emotion: str, action: str, frame: float):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        
        cx = rect.center().x()
        cy = rect.center().y() + 6
        
        body_y_offset = 0
        if action == "jump":
            body_y_offset = -18 * math.sin((frame % 1.0) * math.pi)
        elif action == "dragged":
            body_y_offset = -10
        
        body_color = QColor(215, 185, 145)
        if emotion == "angry":
            body_color = QColor(230, 160, 140)
        elif emotion == "happy":
            body_color = QColor(235, 205, 165)
        
        body_rect = QRectF(cx - 40, cy - 20 + body_y_offset, 80, 55)
        head_rect = QRectF(cx - 35, cy - 52 + body_y_offset, 70, 45)
        
        gradient = QRadialGradient(body_rect.center(), 48)
        gradient.setColorAt(0, body_color.lighter(120))
        gradient.setColorAt(0.6, body_color)
        gradient.setColorAt(1, body_color.darker(115))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(body_rect, 22, 22)
        painter.drawRoundedRect(head_rect, 20, 20)
        
        self._draw_ears(painter, head_rect, body_color.darker(110), emotion, frame)
        self._draw_face(painter, head_rect, emotion, frame)
        self._draw_tail(painter, body_rect, body_color.darker(110), action, frame)
        self._draw_paws(painter, body_rect, body_color.darker(120), action, frame)
        self._draw_collar(painter, body_rect, head_rect)
        
        painter.restore()
    
    def _draw_ears(self, painter, head_rect, color, emotion, frame):
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(150), 1))
        
        droop = 0
        if emotion in ["bored", "shy"]:
            droop = 12
        elif emotion == "happy":
            droop = -6
        
        for i, side in enumerate([-1, 1]):
            ex = head_rect.left() + 8 if i == 0 else head_rect.right() - 8
            ey = head_rect.top() + 6
            
            painter.save()
            path = QPainterPath()
            path.moveTo(ex, ey)
            path.quadTo(ex + side * 22, ey + 16, ex + side * 16, ey + 38 + droop)
            path.quadTo(ex + side * 6, ey + 26, ex, ey + 20)
            path.closeSubpath()
            painter.drawPath(path)
            
            painter.setBrush(QBrush(color.lighter(125)))
            inner = QPainterPath()
            inner.moveTo(ex, ey + 8)
            inner.quadTo(ex + side * 13, ey + 19, ex + side * 11, ey + 30 + droop * 0.5)
            inner.quadTo(ex + side * 4, ey + 23, ex, ey + 18)
            inner.closeSubpath()
            painter.drawPath(inner)
            painter.restore()
            painter.setBrush(QBrush(color))
    
    def _draw_face(self, painter, head_rect, emotion, frame):
        left = QPointF(head_rect.left() + 23, head_rect.top() + 20)
        right = QPointF(head_rect.right() - 23, head_rect.top() + 20)
        
        blink = (frame * 1.4) % 1.0 < 0.1
        eye_h = 3 if blink or emotion == "sleepy" else 10
        
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(100, 80, 60), 1))
        for c in [left, right]:
            painter.drawEllipse(QRectF(c.x() - 7, c.y() - eye_h/2, 14, eye_h))
        
        if not blink and emotion != "sleepy":
            painter.setBrush(QBrush(QColor(50, 30, 20)))
            for c in [left, right]:
                painter.drawEllipse(QRectF(c.x() - 4, c.y() - 4, 8, 8))
                painter.setBrush(QBrush(QColor(255, 255, 255)))
                painter.drawEllipse(QRectF(c.x() - 1, c.y() - 3, 3, 3))
        
        nc = QPointF(head_rect.center().x(), head_rect.top() + 32)
        painter.setBrush(QBrush(QColor(50, 40, 40)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(nc.x() - 8, nc.y() - 5, 16, 12))
        painter.setBrush(QBrush(QColor(255, 255, 255, 80)))
        painter.drawEllipse(QRectF(nc.x() - 5, nc.y() - 3, 5, 4))
        
        mc = QPointF(head_rect.center().x(), head_rect.top() + 39)
        painter.setPen(QPen(QColor(80, 60, 50), 1.5))
        painter.setBrush(Qt.NoBrush)
        
        if emotion == "happy":
            painter.drawArc(QRectF(mc.x() - 13, mc.y(), 26, 14), 180 * 16, 180 * 16)
            painter.setBrush(QBrush(QColor(255, 160, 160, 130)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QRectF(mc.x() - 9, mc.y() + 3, 18, 10))
        elif emotion == "angry":
            painter.drawLine(mc.x() - 9, mc.y() + 5, mc.x() + 9, mc.y() + 5)
        else:
            painter.drawLine(mc.x(), mc.y() - 2, mc.x(), mc.y() + 7)
            painter.drawArc(QRectF(mc.x() - 8, mc.y() + 2, 16, 10), 180 * 16, 120 * 16)
    
    def _draw_tail(self, painter, body_rect, color, action, frame):
        ts = QPointF(body_rect.right() - 6, body_rect.bottom() - 18)
        swing = frame * (5 if action == "happy" else 2)
        angle = swing % 60 - 30
        
        painter.save()
        painter.translate(ts.x(), ts.y())
        painter.rotate(angle - 30)
        
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(150), 1))
        
        th = 22 if action == "happy" else 12
        path = QPainterPath()
        path.moveTo(-5, 0)
        path.quadTo(-7, -16, 0, -th)
        path.quadTo(7, -16, 5, 0)
        path.closeSubpath()
        painter.drawPath(path)
        painter.restore()
    
    def _draw_paws(self, painter, body_rect, color, action, frame):
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        
        t = frame % 1.0
        off = [0, 0]
        if action in ["walk", "run"]:
            s = 6 if action == "run" else 3
            off = [-s * (1 if t < 0.5 else 0), -s * (1 if t >= 0.5 else 0)]
        
        for i, o in enumerate(off):
            x = body_rect.left() + 14 + i * 42
            y = body_rect.bottom() - 6 + o
            painter.drawEllipse(QRectF(x, y, 18, 10))
    
    def _draw_collar(self, painter, body_rect, head_rect):
        cy = head_rect.bottom() + 4
        painter.setBrush(QBrush(QColor(220, 60, 60)))
        painter.setPen(Qt.NoPen)
        painter.drawRect(QRectF(body_rect.left() + 10, cy, body_rect.width() - 20, 8))
        painter.setBrush(QBrush(QColor(255, 215, 0)))
        painter.drawEllipse(QRectF(body_rect.center().x() - 5, cy + 4, 10, 10))


class FoxSkin(SkinBase):
    def draw(self, painter: QPainter, rect: QRectF, state: dict, emotion: str, action: str, frame: float):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        
        cx = rect.center().x()
        cy = rect.center().y() + 5
        
        body_y_offset = 0
        if action == "jump":
            body_y_offset = -20 * math.sin((frame % 1.0) * math.pi)
        elif action == "dragged":
            body_y_offset = -12
        
        body_color = QColor(255, 145, 60)
        if emotion == "angry":
            body_color = QColor(255, 100, 60)
        elif emotion == "shy":
            body_color = QColor(255, 185, 130)
        
        body_rect = QRectF(cx - 36, cy - 24 + body_y_offset, 72, 58)
        head_rect = QRectF(cx - 31, cy - 55 + body_y_offset, 62, 50)
        
        gradient = QRadialGradient(body_rect.center(), 42)
        gradient.setColorAt(0, body_color.lighter(125))
        gradient.setColorAt(0.6, body_color)
        gradient.setColorAt(1, body_color.darker(115))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(body_rect, 18, 18)
        painter.drawRoundedRect(head_rect, 22, 22)
        
        self._draw_ears(painter, head_rect, body_color.darker(120), emotion)
        self._draw_face(painter, head_rect, emotion, frame)
        self._draw_tail(painter, body_rect, body_color, action, frame)
        self._draw_paws(painter, body_rect, QColor(255, 255, 245), action, frame)
        
        painter.restore()
    
    def _draw_ears(self, painter, head_rect, color, emotion):
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(160), 1))
        
        tilt = 0
        if emotion == "angry":
            tilt = 15
        elif emotion == "shy":
            tilt = -12
        
        for i, side in enumerate([-1, 1]):
            ex = head_rect.left() + 12 if i == 0 else head_rect.right() - 12
            ey = head_rect.top() + 2
            
            painter.save()
            painter.translate(ex, ey)
            painter.rotate(side * tilt)
            
            path = QPainterPath()
            path.moveTo(-13, 0)
            path.lineTo(0, -32)
            path.lineTo(13, 0)
            path.closeSubpath()
            painter.drawPath(path)
            
            painter.setBrush(QBrush(QColor(255, 200, 180)))
            inner = QPainterPath()
            inner.moveTo(-8, 0)
            inner.lineTo(0, -24)
            inner.lineTo(8, 0)
            inner.closeSubpath()
            painter.drawPath(inner)
            painter.restore()
            painter.setBrush(QBrush(color))
    
    def _draw_face(self, painter, head_rect, emotion, frame):
        painter.setBrush(QBrush(QColor(255, 255, 240)))
        painter.setPen(Qt.NoPen)
        
        fp = QPainterPath()
        fp.moveTo(head_rect.center().x() - 22, head_rect.top() + 26)
        fp.quadTo(head_rect.center().x(), head_rect.bottom() + 6,
                  head_rect.center().x() + 22, head_rect.top() + 26)
        fp.closeSubpath()
        painter.drawPath(fp)
        
        left = QPointF(head_rect.left() + 20, head_rect.top() + 22)
        right = QPointF(head_rect.right() - 20, head_rect.top() + 22)
        
        blink = (frame * 1.6) % 1.0 < 0.1
        eye_h = 3 if blink or emotion == "sleepy" else 12
        
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(80, 60, 40), 1))
        for c in [left, right]:
            painter.drawEllipse(QRectF(c.x() - 6, c.y() - eye_h/2, 12, eye_h))
        
        if not blink and emotion != "sleepy":
            painter.setBrush(QBrush(QColor(40, 30, 90)))
            for c in [left, right]:
                painter.drawEllipse(QRectF(c.x() - 4, c.y() - 4, 8, 8))
                painter.setBrush(QBrush(QColor(255, 255, 255)))
                painter.drawEllipse(QRectF(c.x() - 2, c.y() - 3, 3, 3))
                painter.setBrush(QBrush(QColor(40, 30, 90)))
        
        nc = QPointF(head_rect.center().x(), head_rect.top() + 35)
        painter.setBrush(QBrush(QColor(50, 30, 30)))
        painter.drawEllipse(QRectF(nc.x() - 5, nc.y() - 4, 10, 8))
        
        painter.setPen(QPen(QColor(80, 60, 40), 1.5))
        painter.setBrush(Qt.NoBrush)
        if emotion == "happy":
            painter.drawArc(QRectF(nc.x() - 10, nc.y() + 2, 20, 11), 180 * 16, 180 * 16)
        else:
            painter.drawLine(nc.x(), nc.y() + 3, nc.x(), nc.y() + 8)
    
    def _draw_tail(self, painter, body_rect, color, action, frame):
        ts = QPointF(body_rect.left() + 6, body_rect.bottom() - 16)
        swing = frame * (3 if action == "happy" else 1.5)
        angle = swing % 40 - 20
        
        painter.save()
        painter.translate(ts.x(), ts.y())
        painter.rotate(30 + angle)
        
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(150), 1))
        
        path = QPainterPath()
        path.moveTo(-9, 0)
        path.quadTo(-6, -26, 10, -42)
        path.quadTo(26, -36, 20, -10)
        path.quadTo(10, 10, 8, 0)
        path.closeSubpath()
        painter.drawPath(path)
        
        painter.setBrush(QBrush(QColor(255, 255, 240)))
        tip = QPainterPath()
        tip.moveTo(10, -36)
        tip.quadTo(22, -32, 20, -20)
        tip.quadTo(14, -25, 10, -36)
        tip.closeSubpath()
        painter.drawPath(tip)
        painter.restore()
    
    def _draw_paws(self, painter, body_rect, color, action, frame):
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        
        t = frame % 1.0
        off = [-4 * (1 if t < 0.5 else 0), -4 * (1 if t >= 0.5 else 0)] if action == "walk" else [0, 0]
        
        for i, o in enumerate(off):
            x = body_rect.left() + 11 + i * 40
            y = body_rect.bottom() - 5 + o
            painter.drawEllipse(QRectF(x, y, 20, 10))


class RobotSkin(SkinBase):
    def draw(self, painter: QPainter, rect: QRectF, state: dict, emotion: str, action: str, frame: float):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        
        cx = rect.center().x()
        cy = rect.center().y() + 5
        
        body_y_offset = 0
        if action == "jump":
            body_y_offset = -22 * math.sin((frame % 1.0) * math.pi)
        elif action == "dragged":
            body_y_offset = -13
        
        base = QColor(155, 165, 185)
        accent = QColor(80, 155, 225)
        if emotion == "angry":
            accent = QColor(225, 80, 80)
        elif emotion == "happy":
            accent = QColor(100, 225, 125)
        
        body_rect = QRectF(cx - 36, cy - 20 + body_y_offset, 72, 60)
        head_rect = QRectF(cx - 33, cy - 58 + body_y_offset, 66, 48)
        
        gradient = QLinearGradient(body_rect.left(), body_rect.top(), body_rect.right(), body_rect.bottom())
        gradient.setColorAt(0, base.lighter(125))
        gradient.setColorAt(0.5, base)
        gradient.setColorAt(1, base.darker(115))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(base.darker(160), 2))
        painter.drawRoundedRect(body_rect, 8, 8)
        painter.drawRoundedRect(head_rect, 10, 10)
        
        self._draw_antenna(painter, head_rect, accent, frame)
        self._draw_screen(painter, head_rect, emotion, frame, accent)
        self._draw_controls(painter, body_rect, accent, frame)
        self._draw_arms_legs(painter, body_rect, base, action, frame)
        
        painter.restore()
    
    def _draw_antenna(self, painter, head_rect, accent, frame):
        ax = head_rect.center().x()
        ay = head_rect.top() - 16 + 4 * math.sin(frame * 2.5)
        
        painter.setPen(QPen(QColor(80, 90, 110), 3))
        painter.drawLine(ax, head_rect.top(), ax, ay)
        
        painter.setBrush(QBrush(accent))
        painter.setPen(QPen(accent.darker(150), 1))
        painter.drawEllipse(QRectF(ax - 5, ay - 5, 10, 10))
        
        glow = QRadialGradient(ax, ay, 16)
        glow.setColorAt(0, accent.lighter(140))
        glow.setColorAt(1, QColor(accent.red(), accent.green(), accent.blue(), 0))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(ax - 13, ay - 13, 26, 26))
    
    def _draw_screen(self, painter, head_rect, emotion, frame, accent):
        screen = QRectF(head_rect.left() + 8, head_rect.top() + 8, head_rect.width() - 16, head_rect.height() - 16)
        
        painter.setBrush(QBrush(QColor(22, 32, 52)))
        painter.setPen(QPen(QColor(55, 65, 85), 2))
        painter.drawRoundedRect(screen, 5, 5)
        
        painter.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 35), 1))
        for y in range(0, int(screen.height()), 4):
            painter.drawLine(screen.left(), screen.top() + y, screen.right(), screen.top() + y)
        
        left_x, right_x = screen.center().x() - 12, screen.center().x() + 12
        eye_y = screen.center().y()
        
        blink = (frame * 1.2) % 1.0 < 0.1
        eye_h = 2 if blink or emotion == "sleepy" else 10
        
        painter.setBrush(QBrush(accent))
        painter.setPen(Qt.NoPen)
        for x in [left_x, right_x]:
            painter.drawRoundedRect(QRectF(x - 6, eye_y - eye_h/2, 12, eye_h), 3, 3)
        
        if emotion != "sleepy" and not blink:
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            for x in [left_x, right_x]:
                painter.drawRect(QRectF(x - 4, eye_y - 4, 3, 3))
        
        mouth_y = eye_y + 14
        painter.setPen(QPen(accent, 2))
        painter.setBrush(Qt.NoBrush)
        
        if emotion == "happy":
            painter.drawArc(QRectF(screen.center().x() - 10, mouth_y - 5, 20, 12), 180 * 16, 180 * 16)
        elif emotion == "angry":
            painter.drawLine(screen.center().x() - 10, mouth_y, screen.center().x() + 10, mouth_y)
            for side in [-1, 1]:
                painter.drawLine(screen.center().x() + side * 15, eye_y - 10,
                                 screen.center().x() + side * 5, eye_y - 5)
        elif emotion == "shy":
            painter.setBrush(QBrush(QColor(255, 150, 150, 100)))
            painter.setPen(Qt.NoPen)
            painter.drawRect(QRectF(screen.left() + 5, mouth_y - 3, 8, 6))
            painter.drawRect(QRectF(screen.right() - 13, mouth_y - 3, 8, 6))
    
    def _draw_controls(self, painter, body_rect, accent, frame):
        painter.setBrush(QBrush(accent))
        painter.setPen(QPen(accent.darker(150), 1))
        painter.drawEllipse(QRectF(body_rect.center().x() - 10, body_rect.top() + 10, 20, 20))
        
        painter.setBrush(QBrush(QColor(255, 255, 255, 100)))
        painter.drawEllipse(QRectF(body_rect.center().x() - 6, body_rect.top() + 12, 8, 8))
        
        lp = (frame * 2.2) % 1.0
        for i in range(3):
            lx = body_rect.center().x() - 18 + i * 18
            la = int(150 + 100 * abs((lp + i * 0.3) % 1.0 - 0.5) * 2)
            painter.setBrush(QBrush(QColor(accent.red(), accent.green(), accent.blue(), la)))
            painter.drawEllipse(QRectF(lx - 3, body_rect.top() + 40, 6, 6))
    
    def _draw_arms_legs(self, painter, body_rect, color, action, frame):
        painter.setBrush(QBrush(color.darker(110)))
        painter.setPen(QPen(color.darker(150), 1))
        
        arm_swing = 0
        if action in ["walk", "run"]:
            s = 3 if action == "run" else 1.5
            arm_swing = 16 * s * (1 if (frame % 1.0) < 0.5 else -1)
        elif action == "dance":
            arm_swing = 25 * math.sin(frame * 4)
        
        for i, side in enumerate([-1, 1]):
            painter.save()
            sx = body_rect.left() if i == 0 else body_rect.right()
            sy = body_rect.top() + 26
            painter.translate(sx, sy)
            painter.rotate(side * arm_swing)
            
            x_off = -8 if i == 0 else 0
            painter.drawRoundedRect(QRectF(side * x_off, -5, 10, 36), 3, 3)
            painter.drawEllipse(QRectF(side * (x_off - 2 if i == 0 else 0), 27, 12, 12))
            painter.restore()
        
        leg_swing = 0
        if action in ["walk", "run"]:
            s = 2 if action == "run" else 1
            leg_swing = 10 * s
        
        for i, side in enumerate([-1, 1]):
            hx = body_rect.left() + 18 if i == 0 else body_rect.right() - 18
            hy = body_rect.bottom() - 6
            sw = leg_swing * (1 if (frame % 1.0) < 0.5 else -1) if action in ["walk", "run"] else 0
            sw *= side
            
            painter.save()
            painter.translate(hx, hy)
            painter.rotate(sw)
            painter.drawRoundedRect(QRectF(-5, 0, 10, 18), 3, 3)
            painter.restore()


class BearSkin(SkinBase):
    def draw(self, painter: QPainter, rect: QRectF, state: dict, emotion: str, action: str, frame: float):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        
        cx = rect.center().x()
        cy = rect.center().y() + 6
        
        body_y_offset = 0
        if action == "jump":
            body_y_offset = -16 * math.sin((frame % 1.0) * math.pi)
        elif action == "dragged":
            body_y_offset = -11
        
        body_color = QColor(165, 125, 95)
        if emotion == "angry":
            body_color = QColor(185, 105, 95)
        elif emotion == "shy":
            body_color = QColor(205, 155, 125)
        
        body_rect = QRectF(cx - 42, cy - 22 + body_y_offset, 84, 66)
        head_rect = QRectF(cx - 37, cy - 56 + body_y_offset, 74, 54)
        
        gradient = QRadialGradient(body_rect.center(), 52)
        gradient.setColorAt(0, body_color.lighter(120))
        gradient.setColorAt(0.6, body_color)
        gradient.setColorAt(1, body_color.darker(115))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(body_rect, 26, 26)
        painter.drawRoundedRect(head_rect, 26, 26)
        
        self._draw_ears(painter, head_rect, body_color)
        self._draw_muzzle(painter, head_rect)
        self._draw_eyes(painter, head_rect, emotion, frame)
        self._draw_nose_mouth(painter, head_rect, emotion)
        self._draw_paws(painter, body_rect, body_color.darker(112), action, frame)
        
        painter.restore()
    
    def _draw_ears(self, painter, head_rect, color):
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(150), 1))
        
        for i, side in enumerate([-1, 1]):
            ex = head_rect.left() + 11 if i == 0 else head_rect.right() - 11
            ey = head_rect.top() - 4
            
            painter.drawEllipse(QRectF(ex - 13, ey - 13, 26, 26))
            painter.setBrush(QBrush(color.darker(120)))
            painter.drawEllipse(QRectF(ex - 8, ey - 8, 16, 16))
            painter.setBrush(QBrush(color))
    
    def _draw_muzzle(self, painter, head_rect):
        painter.setBrush(QBrush(QColor(255, 248, 238)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(head_rect.center().x() - 20, head_rect.top() + 28, 40, 26))
    
    def _draw_eyes(self, painter, head_rect, emotion, frame):
        left = QPointF(head_rect.left() + 24, head_rect.top() + 24)
        right = QPointF(head_rect.right() - 24, head_rect.top() + 24)
        
        blink = (frame * 1.3) % 1.0 < 0.1
        size = 3 if blink or emotion == "sleepy" else 10
        
        painter.setBrush(QBrush(QColor(40, 30, 20)))
        painter.setPen(Qt.NoPen)
        for c in [left, right]:
            painter.drawEllipse(QRectF(c.x() - size/2, c.y() - size/2, size, size))
        
        if not blink and emotion != "sleepy":
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            for c in [left, right]:
                painter.drawEllipse(QRectF(c.x() - 2, c.y() - 3, 3, 3))
    
    def _draw_nose_mouth(self, painter, head_rect, emotion):
        nc = QPointF(head_rect.center().x(), head_rect.top() + 36)
        
        painter.setBrush(QBrush(QColor(60, 40, 40)))
        painter.setPen(Qt.NoPen)
        
        path = QPainterPath()
        path.moveTo(nc.x() - 7, nc.y() - 4)
        path.quadTo(nc.x() - 7, nc.y() + 6, nc.x(), nc.y() + 6)
        path.quadTo(nc.x() + 7, nc.y() + 6, nc.x() + 7, nc.y() - 4)
        path.quadTo(nc.x() + 7, nc.y() - 8, nc.x(), nc.y() - 8)
        path.quadTo(nc.x() - 7, nc.y() - 8, nc.x() - 7, nc.y() - 4)
        painter.drawPath(path)
        
        painter.setBrush(QBrush(QColor(255, 255, 255, 100)))
        painter.drawEllipse(QRectF(nc.x() - 5, nc.y() - 6, 4, 3))
        
        mc = QPointF(head_rect.center().x(), head_rect.top() + 43)
        painter.setPen(QPen(QColor(80, 60, 50), 1.5))
        painter.setBrush(Qt.NoBrush)
        
        painter.drawLine(mc.x(), head_rect.top() + 40, mc.x(), mc.y())
        
        if emotion == "happy":
            painter.drawArc(QRectF(mc.x() - 10, mc.y() - 2, 20, 11), 180 * 16, 180 * 16)
            painter.setBrush(QBrush(QColor(255, 150, 150, 85)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QRectF(head_rect.left() + 9, head_rect.top() + 30, 14, 10))
            painter.drawEllipse(QRectF(head_rect.right() - 23, head_rect.top() + 30, 14, 10))
        elif emotion == "angry":
            painter.drawLine(mc.x() - 8, mc.y() + 5, mc.x() + 8, mc.y() + 5)
    
    def _draw_paws(self, painter, body_rect, color, action, frame):
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        
        t = frame % 1.0
        off = [-4 * (1 if t < 0.5 else 0), -4 * (1 if t >= 0.5 else 0)] if action == "walk" else [0, 0]
        
        for i, o in enumerate(off):
            x = body_rect.left() + 14 + i * 46
            y = body_rect.bottom() - 6 + o
            painter.drawEllipse(QRectF(x, y, 22, 11))


SKINS = {
    "cat": {"name": "小猫咪", "class": CatSkin},
    "dog": {"name": "小狗狗", "class": DogSkin},
    "fox": {"name": "小狐狸", "class": FoxSkin},
    "robot": {"name": "机器人", "class": RobotSkin},
    "bear": {"name": "小熊熊", "class": BearSkin}
}

def get_skin(skin_id: str):
    if skin_id not in SKINS:
        skin_id = "cat"
    return SKINS[skin_id]["class"]()

def get_skin_info():
    emoji = {"cat": "🐱", "dog": "🐕", "fox": "🦊", "robot": "🤖", "bear": "🐻"}
    return {k: {"name": v["name"], "emoji": emoji.get(k, "🐾")} for k, v in SKINS.items()}
