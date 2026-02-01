from pathlib import Path


class SceneManager:
    def __init__(self, webview):
        self.webview = webview

        # Folder where scenes live
        self.scene_path = Path("scenes")

    def load_scene(self, name: str):
        file = self.scene_path / f"{name}.html"

        if not file.exists():
            print("❌ Scene not found:", file)
            return

        html = file.read_text(encoding="utf-8")

        # Inject bridge + wrapper script
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
        </head>

        <body style="font-family: Arial; padding: 20px;">
            <div id="scene">
                {html}
            </div>

            <script>
                let Vertex;

                new QWebChannel(qt.webChannelTransport, function(channel) {{
                    Vertex = channel.objects.bridge;
                    console.log("✅ Vertex Bridge Ready!");
                }});
            </script>
        </body>
        </html>
        """

        print(f"🗺️ Loading Scene: {name}")
        self.webview.setHtml(full_html)
