from __future__ import annotations

def wman() -> WorkerManager:
    assert _WMAN, 'Worker manager must be running when calling wman()'
    return _WMAN

from derpiwallpaper.workers.search import SearchWorker
from derpiwallpaper.workers.wallpaper_updater import WallpaperUpdaterWorker

_WMAN: WorkerManager | None = None

class WorkerManager:
    wp_updater: WallpaperUpdaterWorker
    search: SearchWorker

    def __init__(self) -> None:
        global _WMAN
        assert not _WMAN, 'Only one worker manager can cun at a time.'
        _WMAN = self

        self.wp_updater = WallpaperUpdaterWorker()
        self.search = SearchWorker()
        self.wp_updater.start()
        self.search.start()

    def stop(self):
        global _WMAN

        self.wp_updater.stop()
        self.search.stop()

        _WMAN = None # type: ignore
