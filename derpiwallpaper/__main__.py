import random
import signal
import sys
from time import sleep
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton, QLabel, QVBoxLayout, QWidget, QApplication

from derpiwallpaper.config import CONFIG
from derpiwallpaper.ui import DerpiWallpaperUI
from derpiwallpaper.wallpapermanager import WallpaperManager
from derpiwallpaper.widgetgallery import WidgetGallery

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.hello = ["Hallo Welt", "Hei maailma", "Hola Mundo", "Привет мир"]

        self.button = QPushButton("Click me!")
        self.text = QLabel("Hello World")

        layout = QVBoxLayout(self)
        layout.addWidget(self.text)
        layout.addWidget(self.button)

        self.button.clicked.connect(self.magic)

    @Slot()
    def magic(self):
        self.text.setText(random.choice(self.hello))


if __name__ == "__main__":
    # Initialize wallpaper manager
    wallpaper_manager = WallpaperManager()

    app = QApplication()
    def prepare_exit():
        print("Stopping workers before exiting...")
        wallpaper_manager.updater_worker.stop()
    app.aboutToQuit.connect(prepare_exit)

    # gallery = WidgetGallery()
    # gallery.show()

    widget = DerpiWallpaperUI(wallpaper_manager)

    if "--minimized" in sys.argv:
        if not CONFIG.minimize_to_tray:
            widget.showMinimized()
    else:
        widget.show()


    # Configure signal handling
    def handle_exit_signal(signal_received, frame):
        app.quit()

    signal.signal(signal.SIGINT, handle_exit_signal)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, handle_exit_signal)  # Handle termination

    res = app.exec()
    sys.exit(res)