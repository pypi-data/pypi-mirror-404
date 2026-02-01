from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, QTimer
import json
import functools

class JSBridge(QObject):
    # Core signals
    eventReceived = pyqtSignal(str, str)  # eventName, jsonData
    logMessage = pyqtSignal(str)
    
    def __init__(self, scene_manager):
        super().__init__()
        self.scene_manager = scene_manager
        self._event_listeners = {}  # Python-side listeners
        self._timers = []

    # -----------------------
    # Scene management
    # -----------------------
    @pyqtSlot(str)
    def loadScene(self, name):
        print("🎮 JS Requested Scene:", name)
        self.scene_manager.load_scene(name)
        self.emitEvent("sceneChanged", {"name": name})

    @pyqtSlot(result=str)
    def getCurrentScene(self):
        return self.scene_manager.current_scene

    # -----------------------
    # Event system
    # -----------------------
    @pyqtSlot(str, str)
    def emitEvent(self, event_name, json_data="{}"):
        """Emit event to Python listeners and JS"""
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            data = {"raw": json_data}
        
        # Python-side listeners
        listeners = self._event_listeners.get(event_name, [])
        for callback in listeners:
            callback(data)
        
        # Emit signal to JS
        self.eventReceived.emit(event_name, json.dumps(data))
        print(f"✨ Event emitted: {event_name} → {data}")

    def onEvent(self, event_name, callback):
        """Register Python listener"""
        if event_name not in self._event_listeners:
            self._event_listeners[event_name] = []
        self._event_listeners[event_name].append(callback)
        print(f"✅ Python listener registered for '{event_name}'")

    # -----------------------
    # Logging
    # -----------------------
    @pyqtSlot(str)
    def jsLog(self, message):
        print("📝 JS Log:", message)
        self.logMessage.emit(message)

    # -----------------------
    # Data exchange
    # -----------------------
    @pyqtSlot(str)
    def sendData(self, json_data):
        try:
            data = json.loads(json_data)
            print("📥 Received data from JS:", data)
            self.emitEvent("dataReceived", json_data)
        except json.JSONDecodeError:
            print("❌ Invalid JSON received from JS")

    def updateSceneData(self, data_dict):
        json_str = json.dumps(data_dict)
        self.emitEvent("sceneDataUpdated", json_str)

    # -----------------------
    # Timers / delayed calls
    # -----------------------
    @pyqtSlot(str, int)
    def delayedCall(self, callback_event, delay_ms):
        """Call an event after delay (ms)"""
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(functools.partial(self.emitEvent, callback_event))
        timer.start(delay_ms)
        self._timers.append(timer)
        print(f"⏱ Scheduled delayed event '{callback_event}' in {delay_ms}ms")

    # -----------------------
    # Dynamic JS loading
    # -----------------------
    @pyqtSlot(str, result=str)
    def loadJSModule(self, url):
        """Return the URL to JS for dynamic import (for WebEngine to fetch)"""
        print(f"🌐 JS requested module: {url}")
        # In practice, the JS will do: import(moduleURL)
        return url
