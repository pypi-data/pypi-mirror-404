from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInterceptor

class VertexInterceptor(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        url = info.requestUrl().toString()

        # Block ads/tracking
        blocked_words = ["ads", "doubleclick", "tracker"]

        if any(word in url for word in blocked_words):
            print("🚫 Blocked:", url)
            info.block(True)
