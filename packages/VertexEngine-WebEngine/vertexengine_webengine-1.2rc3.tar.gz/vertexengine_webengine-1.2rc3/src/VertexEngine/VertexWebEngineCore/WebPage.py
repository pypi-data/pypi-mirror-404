from PyQt6.QtWebEngineCore import QWebEnginePage

class VertexWebPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line, source):
        print(f"[JS Console] {message} (Line {line})")

    def acceptNavigationRequest(self, url, nav_type, isMainFrame):
        print("Navigating to:", url.toString())
        return True
