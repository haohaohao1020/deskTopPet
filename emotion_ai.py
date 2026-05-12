import random
from PySide6.QtCore import QObject, Signal, QTimer, Slot

class EmotionAI(QObject):
    emotion_changed = Signal(str)
    stats_changed = Signal(dict)
    need_attention = Signal(str)
    
    EMOTIONS = ["happy", "neutral", "bored", "sleepy", "angry", "shy", "hungry"]
    
    def __init__(self, config_manager):
        super().__init__()
        self._config = config_manager
        
        self._energy = self._config.get("pet", "energy") or 100.0
        self._mood = self._config.get("pet", "mood") or 80.0
        self._hunger = self._config.get("pet", "hunger") or 20.0
        self._emotion = self._config.get("pet", "emotion") or "neutral"
        
        self._idle_time = 0
        self._last_interaction = 0
        
        self._update_timer = QTimer(self)
        self._update_timer.setInterval(1000)
        self._update_timer.timeout.connect(self._update_stats)
        self._update_timer.start()
    
    @property
    def emotion(self):
        return self._emotion
    
    @property
    def energy(self):
        return self._energy
    
    @property
    def mood(self):
        return self._mood
    
    @property
    def hunger(self):
        return self._hunger
    
    def get_stats(self):
        return {
            "emotion": self._emotion,
            "energy": self._energy,
            "mood": self._mood,
            "hunger": self._hunger
        }
    
    @Slot()
    def _update_stats(self):
        self._idle_time += 1
        self._last_interaction += 1
        
        if self._emotion == "sleepy":
            if self._energy < 100:
                self._energy = min(100, self._energy + 0.8)
        elif self._emotion == "neutral":
            if self._energy < 100:
                self._energy = min(100, self._energy + 0.3)
        
        self._hunger = min(100, self._hunger + 0.08)
        
        if self._idle_time > 30:
            self._mood = max(0, self._mood - 0.15)
        
        self._determine_emotion()
        
        self._save_stats()
        self.stats_changed.emit(self.get_stats())
        
        self._check_alerts()
    
    def _determine_emotion(self):
        if self._hunger >= 85:
            new_emotion = "hungry"
        elif self._energy <= 15:
            new_emotion = "sleepy"
        elif self._mood <= 15:
            new_emotion = "angry"
        elif self._mood >= 75 and self._energy >= 50 and self._hunger <= 35:
            new_emotion = "happy"
        elif self._idle_time > 90:
            new_emotion = "bored"
        else:
            new_emotion = "neutral"
        
        if new_emotion != self._emotion:
            self._emotion = new_emotion
            self.emotion_changed.emit(new_emotion)
    
    def _check_alerts(self):
        if self._hunger >= 90 and self._last_interaction > 15:
            self.need_attention.emit("我好饿，快来喂我！")
            self._last_interaction = 0
        elif self._energy <= 10 and self._last_interaction > 15:
            self.need_attention.emit("我好困，想睡觉...")
            self._last_interaction = 0
    
    def _save_stats(self):
        self._config.set("pet", "energy", self._energy)
        self._config.set("pet", "mood", self._mood)
        self._config.set("pet", "hunger", self._hunger)
        self._config.set("pet", "emotion", self._emotion)
    
    @Slot()
    def interact_click(self):
        self._last_interaction = 0
        self._idle_time = 0
        
        if self._emotion == "sleepy":
            self._mood = max(0, self._mood - 12)
            self._emotion = "angry"
            self.emotion_changed.emit("angry")
        elif self._emotion == "angry":
            self._mood = min(100, self._mood + 6)
        else:
            self._mood = min(100, self._mood + 10)
            self._energy = max(0, self._energy - 3)
        
        if random.random() < 0.25:
            self._emotion = "shy"
            self.emotion_changed.emit("shy")
    
    @Slot()
    def interact_hover(self):
        if self._emotion != "sleepy" and random.random() < 0.25:
            self._emotion = "shy"
            self.emotion_changed.emit("shy")
    
    @Slot()
    def feed(self):
        self._last_interaction = 0
        self._idle_time = 0
        self._hunger = max(0, self._hunger - 35)
        self._mood = min(100, self._mood + 15)
        self._emotion = "happy"
        self.emotion_changed.emit("happy")
    
    @Slot()
    def play(self):
        self._last_interaction = 0
        self._idle_time = 0
        self._mood = min(100, self._mood + 20)
        self._energy = max(0, self._energy - 15)
        self._hunger = min(100, self._hunger + 8)
        self._emotion = "happy"
        self.emotion_changed.emit("happy")
    
    @Slot()
    def sleep(self):
        self._emotion = "sleepy"
        self.emotion_changed.emit("sleepy")
    
    @Slot()
    def wake(self):
        self._emotion = "neutral"
        self._idle_time = 0
        self.emotion_changed.emit("neutral")
