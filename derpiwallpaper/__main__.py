import signal
import sys
from PySide6.QtWidgets import QApplication

from derpiwallpaper.config import CONFIG
from derpiwallpaper.ui import DerpiWallpaperUI
from derpiwallpaper.workers import WorkerManager
from derpiwallpaper.workers.wallpaper_updater import WallpaperUpdaterWorker
from derpiwallpaper.widgetgallery import WidgetGallery


if __name__ == "__main__":
    # Initialize wallpaper manager
    workers = WorkerManager()

    app = QApplication()
    def prepare_exit():
        print("Stopping workers before exiting...")
        workers.stop()
    app.aboutToQuit.connect(prepare_exit)

    # gallery = WidgetGallery()
    # gallery.show()

    widget = DerpiWallpaperUI(workers)

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