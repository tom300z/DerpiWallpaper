import signal
import sys
from typing import Callable

from derpiwallpaper.ui import DerpiWallpaperApp
from derpiwallpaper.workers import WorkerManager

if __name__ == "__main__":

    # Configure exit callbacks
    exit_callbacks: set[Callable] = set()
    def prepare_exit():
        for callback in exit_callbacks:
            callback()

    # Initialize the Qt app
    app = DerpiWallpaperApp(start_minimized="--minimized" in sys.argv)
    app.aboutToQuit.connect(prepare_exit)

    try:
        # Initialize wallpaper manager
        workers = WorkerManager()
        def stop_workers():
            print("Stopping workers before exiting...")
            workers.stop()
        exit_callbacks.add(stop_workers)

        # Configure exit signal handling
        def handle_exit_signal(signal_received, frame):
            app.quit()

        signal.signal(signal.SIGINT, handle_exit_signal)  # Handle Ctrl+C
        signal.signal(signal.SIGTERM, handle_exit_signal)  # Handle termination

        # Exit on worker error
        workers.on_error.connect(app.exit_with_error_popup)

        # Run Qt app
        sys.exit(app.exec())
    except Exception as e:
        prepare_exit()
        if isinstance(e, KeyboardInterrupt):
            raise e

        app.exit_with_error_popup(e)
