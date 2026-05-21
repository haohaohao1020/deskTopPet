import time
import math
from enum import Enum
from dataclasses import dataclass, field
from PySide6.QtCore import QObject, Signal, Slot, QTimer


class PawState(Enum):
    IDLE = "idle"
    RAISING = "raising"
    PRESSING = "pressing"
    RELEASING = "releasing"


class MouseAction(Enum):
    NONE = "none"
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    MIDDLE_CLICK = "middle_click"
    SCROLL_UP = "scroll_up"
    SCROLL_DOWN = "scroll_down"


@dataclass
class PawAction:
    state: PawState = PawState.IDLE
    press_offset: float = 0.0
    key_label: str = ""
    key_position: tuple = (0, 0)
    start_time: float = 0.0
    duration: float = 0.0
    is_pressing: bool = False


@dataclass
class MouseVisualState:
    action: MouseAction = MouseAction.NONE
    click_progress: float = 0.0
    scroll_progress: float = 0.0
    start_time: float = 0.0


class ActionStateMachine(QObject):
    left_paw_changed = Signal(float, float, str)
    right_paw_changed = Signal(float, float, str)
    mouse_state_changed = Signal(str, float, float)
    idle_state_changed = Signal(bool)

    DEFAULT_CONFIG = {
        "raise_duration": 0.06,
        "press_duration": 0.04,
        "release_duration": 0.06,
        "min_press_gap": 0.02,
        "rapid_threshold": 0.08,
        "mouse_click_duration": 0.12,
        "mouse_scroll_duration": 0.15,
        "double_tap_speed": 0.12,
        "paw_lift_height": 18.0,
        "paw_press_depth": 8.0,
        "idle_timeout": 1.5,
    }

    def __init__(self, config=None):
        super().__init__()
        self._config = config or self.DEFAULT_CONFIG.copy()

        self._left_paw = PawAction()
        self._right_paw = PawAction()
        self._mouse_state = MouseVisualState()

        self._last_left_time = 0.0
        self._last_right_time = 0.0
        self._last_activity_time = time.time()
        self._is_idle = True

        self._pending_left_queue = []
        self._pending_right_queue = []
        self._left_is_active = False
        self._right_is_active = False

        self._last_left_label = ""
        self._last_right_label = ""

        self._frame_timer = QTimer(self)
        self._frame_timer.setInterval(16)
        self._frame_timer.timeout.connect(self._update_frame)
        self._frame_timer.start()

    @property
    def left_paw(self):
        return self._left_paw

    @property
    def right_paw(self):
        return self._right_paw

    @property
    def mouse_state(self):
        return self._mouse_state

    @property
    def is_idle(self):
        return self._is_idle

    def update_config(self, config: dict):
        self._config.update(config)

    @Slot(str, str, float)
    def on_key_press(self, key: str, paw: str, interval: float):
        now = time.time()
        self._last_activity_time = now
        self._is_idle = False
        self.idle_state_changed.emit(False)

        label = self._format_key_label(key)
        key_pos = self._get_keyboard_position(key)

        if paw in ('left', 'both'):
            self._trigger_paw('left', label, key_pos, now, interval)
        if paw in ('right', 'both'):
            self._trigger_paw('right', label, key_pos, now, interval)

    @Slot(str, str, float)
    def on_key_release(self, key: str, paw: str, duration: float):
        now = time.time()
        self._last_activity_time = now

    @Slot(str, int, float)
    def on_mouse_click(self, button: str, pressed: int, event_time: float):
        now = time.time()
        self._last_activity_time = now
        self._is_idle = False
        self.idle_state_changed.emit(False)

        if pressed:
            action_map = {
                'left': MouseAction.LEFT_CLICK,
                'right': MouseAction.RIGHT_CLICK,
                'middle': MouseAction.MIDDLE_CLICK,
            }
            action = action_map.get(button, MouseAction.LEFT_CLICK)
            self._mouse_state = MouseVisualState(
                action=action,
                click_progress=0.0,
                scroll_progress=0.0,
                start_time=now,
            )
            self.mouse_state_changed.emit(
                action.value, 0.0, 0.0
            )

    @Slot(int, float)
    def on_mouse_scroll(self, direction: int, event_time: float):
        now = time.time()
        self._last_activity_time = now
        self._is_idle = False
        self.idle_state_changed.emit(False)

        action = MouseAction.SCROLL_UP if direction > 0 else MouseAction.SCROLL_DOWN
        self._mouse_state = MouseVisualState(
            action=action,
            click_progress=0.0,
            scroll_progress=0.0,
            start_time=now,
        )
        self.mouse_state_changed.emit(
            action.value, 0.0, float(direction)
        )

    def _trigger_paw(self, side: str, label: str, key_pos: tuple, now: float, interval: float):
        if side == 'left':
            paw = self._left_paw
            last_time = self._last_left_time
            is_active = self._left_is_active
        else:
            paw = self._right_paw
            last_time = self._last_right_time
            is_active = self._right_is_active

        min_gap = self._config.get("min_press_gap", 0.02)
        rapid_threshold = self._config.get("rapid_threshold", 0.08)

        is_rapid = (now - last_time) < rapid_threshold if last_time > 0 else False

        if is_active and (now - last_time) < min_gap:
            return

        press_depth = self._config.get("paw_press_depth", 8.0)
        if is_rapid:
            press_depth *= 0.6

        paw.state = PawState.RAISING
        paw.key_label = label
        paw.key_position = key_pos
        paw.press_offset = 0.0
        paw.start_time = now
        paw.is_pressing = True

        if side == 'left':
            self._left_is_active = True
            self._last_left_time = now
            self._last_left_label = label
            self._schedule_paw_release('left')
        else:
            self._right_is_active = True
            self._last_right_time = now
            self._last_right_label = label
            self._schedule_paw_release('right')

    def _schedule_paw_release(self, side: str):
        raise_dur = self._config.get("raise_duration", 0.06)
        press_dur = self._config.get("press_duration", 0.04)
        total = int((raise_dur + press_dur) * 1000)
        if side == 'left':
            QTimer.singleShot(total, lambda: self._complete_press('left'))
        else:
            QTimer.singleShot(total, lambda: self._complete_press('right'))

    def _complete_press(self, side: str):
        now = time.time()
        if side == 'left':
            paw = self._left_paw
            self._left_is_active = False
        else:
            paw = self._right_paw
            self._right_is_active = False

        paw.state = PawState.RELEASING
        paw.start_time = now

        release_dur = int(self._config.get("release_duration", 0.06) * 1000)
        if side == 'left':
            QTimer.singleShot(release_dur, lambda: self._reset_paw('left'))
        else:
            QTimer.singleShot(release_dur, lambda: self._reset_paw('right'))

    def _reset_paw(self, side: str):
        if side == 'left':
            self._left_paw = PawAction()
        else:
            self._right_paw = PawAction()

    def _update_frame(self):
        now = time.time()

        for side, paw in [('left', self._left_paw), ('right', self._right_paw)]:
            if not paw.is_pressing and paw.state == PawState.IDLE:
                continue

            total_cycle = (
                self._config.get("raise_duration", 0.06) +
                self._config.get("press_duration", 0.04) +
                self._config.get("release_duration", 0.06)
            )

            elapsed = now - paw.start_time
            t = min(elapsed / max(total_cycle, 0.001), 1.0)

            lift_h = self._config.get("paw_lift_height", 18.0)
            press_d = self._config.get("paw_press_depth", 8.0)

            raise_t = self._config.get("raise_duration", 0.06) / total_cycle
            press_t = raise_t + self._config.get("press_duration", 0.04) / total_cycle

            offset = 0.0
            if t < raise_t:
                sub = t / max(raise_t, 0.001)
                offset = lift_h * math.sin(sub * math.pi * 0.5)
            elif t < press_t:
                sub = (t - raise_t) / max(press_t - raise_t, 0.001)
                offset = lift_h - (lift_h + press_d) * math.sin(sub * math.pi * 0.5)
            elif t < 1.0:
                sub = (t - press_t) / max(1.0 - press_t, 0.001)
                offset = -press_d * math.cos(sub * math.pi * 0.5)

            if side == 'left':
                self.left_paw_changed.emit(offset, t, paw.key_label)
            else:
                self.right_paw_changed.emit(offset, t, paw.key_label)

        if self._mouse_state.action != MouseAction.NONE:
            elapsed = now - self._mouse_state.start_time
            click_dur = self._config.get("mouse_click_duration", 0.12)
            scroll_dur = self._config.get("mouse_scroll_duration", 0.15)

            action = self._mouse_state.action
            if action in (MouseAction.SCROLL_UP, MouseAction.SCROLL_DOWN):
                t = min(elapsed / scroll_dur, 1.0)
                self._mouse_state.scroll_progress = t
                self.mouse_state_changed.emit(
                    action.value, 0.0, self._mouse_state.scroll_progress
                )
                if t >= 1.0:
                    self._mouse_state = MouseVisualState()
            else:
                t = min(elapsed / click_dur, 1.0)
                self._mouse_state.click_progress = t
                self.mouse_state_changed.emit(
                    action.value, self._mouse_state.click_progress, 0.0
                )
                if t >= 1.0:
                    self._mouse_state = MouseVisualState()

        if self._is_idle:
            return

        idle_timeout = self._config.get("idle_timeout", 1.5)
        if (now - self._last_activity_time) > idle_timeout:
            if not self._left_is_active and not self._right_is_active:
                if self._mouse_state.action == MouseAction.NONE:
                    self._is_idle = True
                    self.idle_state_changed.emit(True)

    def _format_key_label(self, key: str) -> str:
        label_map = {
            'Key.space': 'SPC',
            'Key.enter': 'ENT',
            'Key.backspace': 'BSP',
            'Key.shift_l': 'SFT',
            'Key.shift_r': 'SFT',
            'Key.ctrl_l': 'CTL',
            'Key.ctrl_r': 'CTL',
            'Key.alt_l': 'ALT',
            'Key.alt_r': 'ALT',
            'Key.tab': 'TAB',
            'Key.esc': 'ESC',
            'Key.caps_lock': 'CAP',
            'Key.up': '↑',
            'Key.down': '↓',
            'Key.left': '←',
            'Key.right': '→',
        }
        if key in label_map:
            return label_map[key]
        if key.startswith('Key.'):
            part = key.split('.')[-1]
            if len(part) == 1:
                return part.upper()
            if part.startswith('f') and part[1:].isdigit():
                return part.upper()
            return part[:3].upper()
        return '??'

    def _get_keyboard_position(self, key: str) -> tuple:
        key_positions = {
            'Key.q': (0, 0), 'Key.w': (1, 0), 'Key.e': (2, 0),
            'Key.r': (3, 0), 'Key.t': (4, 0),
            'Key.a': (0, 1), 'Key.s': (1, 1), 'Key.d': (2, 1),
            'Key.f': (3, 1), 'Key.g': (4, 1),
            'Key.z': (0, 2), 'Key.x': (1, 2), 'Key.c': (2, 2),
            'Key.v': (3, 2),
            'Key.y': (5, 0), 'Key.u': (6, 0), 'Key.i': (7, 0),
            'Key.o': (8, 0), 'Key.p': (9, 0),
            'Key.h': (5, 1), 'Key.j': (6, 1), 'Key.k': (7, 1),
            'Key.l': (8, 1),
            'Key.b': (5, 2), 'Key.n': (6, 2), 'Key.m': (7, 2),
            'Key.space': (4, 3),
            'Key.enter': (9, 1),
            'Key.backspace': (9, 2),
            'Key.shift_l': (0, 3),
            'Key.ctrl_l': (0, 3),
        }
        return key_positions.get(key, (4, 3))
