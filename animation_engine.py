import random
import math
from PySide6.QtCore import QObject, QTimer, Signal, Slot, QPoint, QRect, Qt, QGuiApplication

class AnimationEngine(QObject):
    action_changed = Signal(str)
    position_changed = Signal(int, int)
    frame_updated = Signal(float)
    
    ACTIONS = ["idle", "walk", "run", "jump", "sit", "sleep", "dragged", "dance", "sneeze", "stretch", "spin", "happy"]
    
    def __init__(self, config_manager, screen_geometry: QRect):
        super().__init__()
        self._config = config_manager
        self._screen = screen_geometry
        
        self._current_action = "idle"
        self._action_duration = 0
        self._frame = 0.0
        self._fps = 60
        
        self._position = QPoint(
            self._config.get("window", "x") or 500,
            self._config.get("window", "y") or 300
        )
        self._velocity = QPoint(0, 0)
        self._direction = 1
        
        self._walk_timer = 0
        self._idle_variation = 0
        self._special_action_chance = 0.004
        
        self._animation_timer = QTimer(self)
        self._animation_timer.setInterval(int(1000 / self._fps))
        self._animation_timer.timeout.connect(self._update_animation)
        self._animation_timer.start()
        
        self._pending_special = None
    
    @property
    def current_action(self):
        return self._current_action
    
    @property
    def position(self):
        return self._position
    
    @property
    def frame(self):
        return self._frame
    
    def set_position(self, x: int, y: int):
        self._position = QPoint(x, y)
        self.position_changed.emit(x, y)
    
    @Slot()
    def _update_animation(self):
        self._frame += 1.0 / self._fps
        self.frame_updated.emit(self._frame)
        
        if self._current_action not in ["dragged", "dance", "sneeze", "stretch", "spin"]:
            self._update_movement()
            self._update_action_selection()
        
        if self._action_duration % 300 == 0:
            self._save_position()
    
    def _update_movement(self):
        if self._current_action == "walk":
            self._position.setX(self._position.x() + self._direction * 2)
            self._check_screen_bounds()
        elif self._current_action == "run":
            self._position.setX(self._position.x() + self._direction * 5)
            self._check_screen_bounds()
        
        self.position_changed.emit(self._position.x(), self._position.y())
    
    def _check_screen_bounds(self):
        ww = self._config.get("window", "width") or 120
        wh = self._config.get("window", "height") or 120
        
        snap_dist = self._config.get("window", "snap_distance") or 20
        edge_snap = self._config.get("window", "edge_snap")
        
        if self._position.x() < snap_dist:
            if edge_snap:
                self._position.setX(0)
            self._direction = 1
            self._action_duration = 0
        elif self._position.x() + ww > self._screen.width() - snap_dist:
            if edge_snap:
                self._position.setX(self._screen.width() - ww)
            self._direction = -1
            self._action_duration = 0
        
        if self._position.y() < snap_dist:
            if edge_snap:
                self._position.setY(0)
        elif self._position.y() + wh > self._screen.height() - snap_dist:
            if edge_snap:
                self._position.setY(self._screen.height() - wh - 50)
    
    def _update_action_selection(self):
        self._action_duration += 1
        
        if self._action_duration > self._get_action_duration(self._current_action):
            self._action_duration = 0
            self._choose_next_action()
    
    def _get_action_duration(self, action: str) -> int:
        d = {
            "idle": random.randint(80, 200),
            "walk": random.randint(70, 140),
            "run": random.randint(40, 80),
            "jump": 35,
            "sit": random.randint(150, 280),
            "sleep": random.randint(400, 700),
            "happy": 80
        }
        return d.get(action, 80)
    
    def _choose_next_action(self):
        if random.random() < self._special_action_chance:
            sp = ["sneeze", "stretch", "spin"]
            self._start_special_action(random.choice(sp))
            return
        
        w = {"idle": 42, "walk": 26, "sit": 14, "run": 9, "jump": 9}
        total = sum(w.values())
        r = random.randint(1, total)
        cum = 0
        
        for act, weight in w.items():
            cum += weight
            if r <= cum:
                self._set_action(act)
                break
    
    def _set_action(self, action: str):
        if action != self._current_action:
            self._current_action = action
            self._action_duration = 0
            self.action_changed.emit(action)
            
            if action in ["walk", "run"]:
                self._direction = random.choice([-1, 1])
    
    def _start_special_action(self, action: str):
        self._current_action = action
        self._action_duration = 0
        self.action_changed.emit(action)
        
        dm = {"sneeze": 70, "stretch": 100, "spin": 130, "dance": 200}
        dur = dm.get(action, 70)
        
        QTimer.singleShot(dur * int(1000 / self._fps), self._on_special_done)
    
    @Slot()
    def _on_special_done(self):
        self._set_action("idle")
    
    def _save_position(self):
        self._config.set("window", "x", self._position.x())
        self._config.set("window", "y", self._position.y())
    
    @Slot()
    def on_click(self):
        self._set_action("happy")
        QTimer.singleShot(1200, self._on_happy_done)
    
    @Slot()
    def _on_happy_done(self):
        self._set_action("idle")
    
    @Slot()
    def on_double_click(self):
        self._start_special_action("dance")
    
    @Slot()
    def on_drag_start(self):
        self._set_action("dragged")
    
    @Slot()
    def on_drag_end(self):
        self._set_action("idle")
    
    @Slot()
    def on_hover(self):
        if self._current_action == "idle" and random.random() < 0.35:
            self._idle_variation = random.choice([0, 1, 2])
    
    def set_emotion_context(self, emotion: str):
        if emotion == "sleepy" and self._current_action not in ["dragged", "dance"]:
            self._set_action("sleep")
        elif emotion == "angry" and self._current_action == "sleep":
            self._set_action("idle")
