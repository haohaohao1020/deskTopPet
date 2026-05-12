import sys
import json
import time
from datetime import datetime
from PySide6.QtCore import QThread, Signal, Slot, QObject

try:
    import urllib.request
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False

try:
    import winreg
    HAS_WINREG = True
except ImportError:
    HAS_WINREG = False


class WeatherWorker(QThread):
    weather_ready = Signal(dict)
    weather_error = Signal(str)
    
    def __init__(self, city: str = "auto"):
        super().__init__()
        self._city = city
        self._running = False
    
    def run(self):
        self._running = True
        while self._running:
            try:
                data = self._fetch_weather()
                if data:
                    self.weather_ready.emit(data)
            except Exception as e:
                self.weather_error.emit(str(e))
            
            for _ in range(1800):
                if not self._running:
                    break
                self.msleep(100)
    
    def _fetch_weather(self) -> dict:
        if not HAS_URLLIB:
            return self._mock()
        
        try:
            url = "https://wttr.in/?format=j1"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if isinstance(data, list) and data:
                    cur = data[0].get('current_condition', [{}])[0]
                    desc = cur.get('lang_zh', [{}])[0].get('value', 
                             cur.get('weatherDesc', [{}])[0].get('value', 'N/A'))
                    return {'temp': cur.get('temp_C', 'N/A'), 'desc': desc,
                            'humidity': cur.get('humidity', 'N/A'), 'city': self._city}
            return self._mock()
        except Exception:
            return self._mock()
    
    def _mock(self) -> dict:
        conds = ['晴朗', '多云', '阴天', '小雨', '微风']
        return {'temp': str(18 + int(time.time()) % 12),
                'desc': conds[int(time.time()) % len(conds)],
                'humidity': str(45 + int(time.time()) % 35), 'city': '本地'}
    
    def stop(self):
        self._running = False


class ReminderWorker(QThread):
    reminder_triggered = Signal(str, str)
    
    def __init__(self, reminders: list):
        super().__init__()
        self._reminders = reminders.copy()
        self._running = False
        self._triggered = set()
    
    def set_reminders(self, reminders: list):
        self._reminders = reminders.copy()
        self._triggered.clear()
    
    def run(self):
        self._running = True
        while self._running:
            now = datetime.now()
            t = now.strftime("%H:%M")
            d = now.weekday()
            
            for idx, r in enumerate(self._reminders):
                if r.get('time') == t:
                    key = f"{idx}_{t}_{now.date()}"
                    if key not in self._triggered:
                        days = r.get('days', list(range(7)))
                        if d in days:
                            self.reminder_triggered.emit(r.get('title', '提醒'), r.get('message', ''))
                            self._triggered.add(key)
            
            self.msleep(30000)
    
    def stop(self):
        self._running = False


class AutoStartManager(QObject):
    status_changed = Signal(bool)
    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "DesktopPet"
    
    def __init__(self):
        super().__init__()
    
    @Slot()
    def enable(self):
        if not HAS_WINREG:
            return
        path = sys.executable
        if not getattr(sys, 'frozen', False):
            path = f'"{sys.executable}" "{sys.argv[0]}"'
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REG_PATH, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, self.APP_NAME, 0, winreg.REG_SZ, path)
            winreg.CloseKey(key)
            self.status_changed.emit(True)
        except Exception as e:
            print(f"启用自启失败: {e}")
    
    @Slot()
    def disable(self):
        if not HAS_WINREG:
            return
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REG_PATH, 0, winreg.KEY_SET_VALUE)
            try:
                winreg.DeleteValue(key, self.APP_NAME)
            except FileNotFoundError:
                pass
            winreg.CloseKey(key)
            self.status_changed.emit(False)
        except Exception as e:
            print(f"禁用自启失败: {e}")
    
    def is_enabled(self) -> bool:
        if not HAS_WINREG:
            return False
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REG_PATH, 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, self.APP_NAME)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception:
            return False
