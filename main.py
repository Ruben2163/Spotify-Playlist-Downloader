import sys
from PyQt5.QtWidgets import QApplication
from gui import DownloaderApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DownloaderApp()
    window.show()
    sys.exit(app.exec_())
