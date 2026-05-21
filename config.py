import os
import json
import sys
from PySide6.QtCore import QObject, Signal

class ConfigManager(QObject):
    config_changed = Signal(dict)
    
    DEFAULT_CONFIG = {
        "window": {
            "x": 500,
            "y": 300,
            "width": 120,
            "height": 120,
            "scale": 1.0,
            "opacity": 1.0,
            "always_on_top": True,
            "click_through": False,
            "edge_snap": True,
            "snap_distance": 20
        },
        "pet": {
            "current_skin": "cat",
            "energy": 100.0,
            "mood": 80.0,
            "hunger": 20.0,
            "emotion": "happy",
            "auto_sleep": True,
            "idle_timeout": 180
        },
        "bongocat": {
            "enabled": False,
            "raise_duration": 0.06,
            "press_duration": 0.04,
            "release_duration": 0.06,
            "min_press_gap": 0.02,
            "rapid_threshold": 0.08,
            "mouse_click_duration": 0.12,
            "mouse_scroll_duration": 0.15,
            "paw_lift_height": 18.0,
            "paw_press_depth": 8.0,
            "idle_timeout": 1.5
        },
        "system": {
            "auto_start": False,
            "show_weather": True,
            "reminders": [],
            "language": "zh_CN"
        }
    }
    
    def __init__(self):
        super().__init__()
        self._config = {}
        self._config_path = self._get_config_path()
        self._load_config()
    
    def _get_config_path(self):
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, "pet_config.json")
    
    def _load_config(self):
        try:
            if os.path.exists(self._config_path):
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                self._merge_defaults()
            else:
                self._config = json.loads(json.dumps(self.DEFAULT_CONFIG))
                self._save_config()
        except Exception as e:
            print(f"加载配置失败: {e}")
            self._config = json.loads(json.dumps(self.DEFAULT_CONFIG))
    
    def _merge_defaults(self):
        for cat, defaults in self.DEFAULT_CONFIG.items():
            if cat not in self._config:
                self._config[cat] = defaults.copy()
            else:
                for key, val in defaults.items():
                    if key not in self._config[cat]:
                        self._config[cat][key] = val
    
    def _save_config(self):
        try:
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get(self, category, key=None):
        if category not in self._config:
            return None
        if key is None:
            return self._config[category]
        return self._config[category].get(key)
    
    def set(self, category, key, value):
        if category not in self._config:
            self._config[category] = {}
        self._config[category][key] = value
        self._save_config()
        self.config_changed.emit({category: {key: value}})
    
    def update(self, category, values):
        if category not in self._config:
            self._config[category] = {}
        self._config[category].update(values)
        self._save_config()
        self.config_changed.emit({category: values})
