from __future__ import annotations

from PySide6.QtCore import QThread, Signal, SignalInstance, QObject


def wman() -> WorkerManager:
    assert _WMAN, 'Worker manager must be running when calling wman()'
    return _WMAN

from time import sleep

class WorkerThread(QThread):
    update_ui: SignalInstance = Signal()  # type: ignore # Signal to notify about updates
    on_error: SignalInstance = Signal(Exception)  # type: ignore # Signal to notify about errors

    def __init__(self) -> None:
        super().__init__()

    def on_tick(self):
        """Perform work in each tick."""
        pass

    def run(self) -> None:
        """Run the worker thread."""
        while not self.isInterruptionRequested():
            try:
                self.on_tick()
            except Exception as e:
                self.on_error.emit(e)
                raise e
            sleep(0.1)

    def stop(self):
        """Stop the worker thread."""
        self.requestInterruption()  # Request the thread to stop
        self.wait()  # Optionally wait for the thread to finish

from derpiwallpaper.workers.search import SearchWorker
from derpiwallpaper.workers.wallpaper_updater import WallpaperUpdaterWorker

_WMAN: WorkerManager | None = None

class WorkerManager(QObject):
    wp_updater: WallpaperUpdaterWorker
    search: SearchWorker
    on_error: SignalInstance = Signal(Exception) # type: ignore

    def __init__(self) -> None:
        super().__init__()

        global _WMAN
        assert not _WMAN, 'Only one worker manager can cun at a time.'
        _WMAN = self

        self.search = SearchWorker()
        self.search.on_error.connect(self.on_error.emit)
        self.wp_updater = WallpaperUpdaterWorker()
        self.wp_updater.on_error.connect(self.on_error.emit)

        self.search.start()
        self.wp_updater.start()

    def stop(self):
        global _WMAN

        self.wp_updater.stop()
        self.search.stop()

        _WMAN = None # type: ignore
