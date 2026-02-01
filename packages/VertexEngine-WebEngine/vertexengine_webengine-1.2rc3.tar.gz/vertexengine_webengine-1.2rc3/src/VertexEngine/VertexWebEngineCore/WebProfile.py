from PyQt6.QtWebEngineCore import QWebEngineProfile

class VertexProfile(QWebEngineProfile):
    def __init__(self):
        super().__init__("MyBrowserProfile")

        self.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )

        self.setCachePath("cache/")
        self.setPersistentStoragePath("storage/")

        print("Profile Loaded ✅")
