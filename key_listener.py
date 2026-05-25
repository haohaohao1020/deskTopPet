import time
from collections import deque
from PySide6.QtCore import QObject, Signal, Slot, QThread

try:
    from pynput import keyboard, mouse
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False
    print("[WARN] pynput not installed. Run: pip install pynput")


LEFT_HAND_KEYS = {
    'Key.q', 'Key.w', 'Key.e', 'Key.r', 'Key.t',
    'Key.a', 'Key.s', 'Key.d', 'Key.f', 'Key.g',
    'Key.z', 'Key.x', 'Key.c', 'Key.v',
    'Key.shift_l', 'Key.ctrl_l',
}

RIGHT_HAND_KEYS = {
    'Key.y', 'Key.u', 'Key.i', 'Key.o', 'Key.p',
    'Key.h', 'Key.j', 'Key.k', 'Key.l',
    'Key.b', 'Key.n', 'Key.m',
    'Key.enter', 'Key.backspace',
}

BOTH_PAW_KEYS = {
    'Key.space',
    'Key.up', 'Key.down', 'Key.left', 'Key.right',
    'Key.0', 'Key.1', 'Key.2', 'Key.3', 'Key.4',
    'Key.5', 'Key.6', 'Key.7', 'Key.8', 'Key.9',
    'Key.f1', 'Key.f2', 'Key.f3', 'Key.f4', 'Key.f5',
    'Key.f6', 'Key.f7', 'Key.f8', 'Key.f9', 'Key.f10',
    'Key.f11', 'Key.f12',
    'Key.tab', 'Key.esc', 'Key.caps_lock',
}


def _normalize_key(key):
    try:
        if hasattr(key, 'char') and key.char:
            return f'Key.{key.char.lower()}'
        if hasattr(key, 'name'):
            name = key.name
            if name in ('shift', 'ctrl', 'alt', 'cmd'):
                pass
            return f'Key.{name}'
        return str(key)
    except Exception:
        return str(key)


def _classify_key(normalized):
    if normalized in LEFT_HAND_KEYS:
        return 'left'
    if normalized in RIGHT_HAND_KEYS:
        return 'right'
    if normalized in BOTH_PAW_KEYS:
        return 'both'
    if normalized.startswith('Key.shift') or normalized.startswith('Key.ctrl'):
        if '_l' in normalized:
            return 'left'
        elif '_r' in normalized:
            return 'right'
        return 'both'
    if normalized.startswith('Key.alt'):
        if '_l' in normalized:
            return 'left'
        elif '_r' in normalized:
            return 'right'
        return 'both'
    if len(normalized) == len('Key.x') and normalized.startswith('Key.'):
        ch = normalized.split('.')[-1]
        if ch in 'qwertasdfgzxcv':
            return 'left'
        if ch in 'yuiophjklbnm':
            return 'right'
    return 'both'


class KeyListener(QObject):
    key_pressed = Signal(str, str, float)
    key_released = Signal(str, str, float)
    mouse_clicked = Signal(str, int, float)
    mouse_scrolled = Signal(int, float)
    ctrl_pressed = Signal()
    ctrl_released = Signal()

    MAX_HISTORY = 200

    def __init__(self):
        super().__init__()
        self._kb_listener = None
        self._ms_listener = None
        self._running = False
        self._press_times = {}
        self._event_history = deque(maxlen=self.MAX_HISTORY)
        self._last_key_time = 0.0

    @Slot()
    def start(self):
        if not HAS_PYNPUT or self._running:
            return
        self._running = True
        try:
            self._kb_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release,
            )
            self._kb_listener.daemon = True
            self._kb_listener.start()

            self._ms_listener = mouse.Listener(
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll,
            )
            self._ms_listener.daemon = True
            self._ms_listener.start()
            print("[INFO] KeyListener started (global keyboard+mouse listening)")
        except Exception as e:
            print(f"[ERROR] KeyListener start failed: {e}")
            self._running = False

    @Slot()
    def stop(self):
        self._running = False
        try:
            if self._kb_listener:
                self._kb_listener.stop()
                self._kb_listener = None
            if self._ms_listener:
                self._ms_listener.stop()
                self._ms_listener = None
            print("[INFO] KeyListener stopped")
        except Exception as e:
            print(f"[ERROR] KeyListener stop failed: {e}")

    def _on_key_press(self, key):
        if not self._running:
            return
        try:
            normalized = _normalize_key(key)
            now = time.time()
            paw = _classify_key(normalized)
            interval = now - self._last_key_time if self._last_key_time > 0 else 0.0
            self._last_key_time = now
            self._press_times[normalized] = now
            self._event_history.append({
                'type': 'press',
                'key': normalized,
                'paw': paw,
                'time': now,
                'interval': interval,
            })
            self.key_pressed.emit(normalized, paw, interval)
            
            if normalized in ['Key.ctrl_l', 'Key.ctrl_r', 'Key.ctrl']:
                self.ctrl_pressed.emit()
        except Exception:
            pass

    def _on_key_release(self, key):
        if not self._running:
            return
        try:
            normalized = _normalize_key(key)
            now = time.time()
            paw = _classify_key(normalized)
            press_time = self._press_times.pop(normalized, now)
            duration = now - press_time
            self._event_history.append({
                'type': 'release',
                'key': normalized,
                'paw': paw,
                'time': now,
                'duration': duration,
            })
            self.key_released.emit(normalized, paw, duration)
            
            if normalized in ['Key.ctrl_l', 'Key.ctrl_r', 'Key.ctrl']:
                self.ctrl_released.emit()
        except Exception:
            pass

    def _on_mouse_click(self, x, y, button, pressed):
        if not self._running:
            return
        try:
            now = time.time()
            btn_name = button.name if hasattr(button, 'name') else str(button)
            action = 'press' if pressed else 'release'
            self._event_history.append({
                'type': f'mouse_{action}',
                'button': btn_name,
                'time': now,
            })
            self.mouse_clicked.emit(btn_name, 1 if pressed else 0, now)
        except Exception:
            pass

    def _on_mouse_scroll(self, x, y, dx, dy):
        if not self._running:
            return
        try:
            now = time.time()
            self.mouse_scrolled.emit(int(dy), now)
        except Exception:
            pass

    @property
    def last_key_interval(self):
        return self._last_key_time

    @property
    def event_history(self):
        return list(self._event_history)


class ListenerThread(QThread):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._listener = KeyListener()

    @property
    def listener(self):
        return self._listener

    def run(self):
        self._listener.start()
        self.exec()

    def stop_listener(self):
        self._listener.stop()
        self.quit()
        self.wait(1000)
