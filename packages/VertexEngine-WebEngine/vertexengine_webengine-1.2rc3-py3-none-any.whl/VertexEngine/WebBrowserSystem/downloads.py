import os

class DownloadManager:
    def __init__(self):
        self.download_folder = "downloads/"
        os.makedirs(self.download_folder, exist_ok=True)

    def handle_download(self, download):
        filename = download.downloadFileName()

        download.setDownloadDirectory(self.download_folder)
        download.accept()

        print("📥 Downloading:", filename)
