from PyQt6.QtWidgets import QToolBar, QLineEdit
from PyQt6.QtGui import QAction

class NavBar(QToolBar):
    def __init__(self, tabs):
        super().__init__()

        self.tabs = tabs

        # Buttons
        back_btn = QAction("⬅", self)
        forward_btn = QAction("➡", self)
        reload_btn = QAction("🔄", self)
        newtab_btn = QAction("➕", self)

        back_btn.triggered.connect(lambda: self.current().back())
        forward_btn.triggered.connect(lambda: self.current().forward())
        reload_btn.triggered.connect(lambda: self.current().reload())
        newtab_btn.triggered.connect(lambda: self.tabs.add_new_tab())

        self.addAction(back_btn)
        self.addAction(forward_btn)
        self.addAction(reload_btn)
        self.addAction(newtab_btn)

        # URL Bar
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.load_url)
        self.addWidget(self.url_bar)

    def current(self):
        return self.tabs.currentWidget()

    def load_url(self):
        url = self.url_bar.text()
        if not url.startswith("http"):
            url = "https://" + url

        self.current().load(url)
