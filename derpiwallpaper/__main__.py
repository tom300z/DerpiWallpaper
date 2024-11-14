import signal
import sys

from derpiwallpaper.config import CONFIG
from derpiwallpaper.ui import DerpiWallpaperApp
from derpiwallpaper.workers import WorkerManager


if __name__ == "__main__":
    # Initialize wallpaper manager
    workers = WorkerManager()

    # Start Qt app
    app = DerpiWallpaperApp(start_minimized="--minimized" in sys.argv)
    def prepare_exit():
        print("Stopping workers before exiting...")
        workers.stop()
    app.aboutToQuit.connect(prepare_exit)

    # Configure exit signal handling
    def handle_exit_signal(signal_received, frame):
        app.quit()

    signal.signal(signal.SIGINT, handle_exit_signal)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, handle_exit_signal)  # Handle termination

    # Exit on worker error
    workers.on_error.connect(app.exit_with_error_popup)

    # Run Qt app
    try:
        sys.exit(app.exec())
    except Exception as e:
        prepare_exit()
        if isinstance(e, KeyboardInterrupt):
            raise e

        app.exit_with_error_popup(e)
