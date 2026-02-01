from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from VertexWebEngineCore.WebScene import SceneManager
from VertexWebEngineCore.JSBridge import JSBridge

class WebEngine(QWebEngineView):
    def __init__(self):
        super().__init__()

        # Scene system
        self.scene_manager = SceneManager(self)

        # Bridge
        self.bridge = JSBridge(self.scene_manager)

        # Channel
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)

        self.page().setWebChannel(self.channel)

        # Start on menu
        self.scene_manager.load_scene("menu")
