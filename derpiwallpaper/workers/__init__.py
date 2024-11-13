from derpiwallpaper.workers.search import SearchWorker
from derpiwallpaper.workers.wallpaper_updater import WallpaperUpdaterWorker


class WorkerManager:
    wp_updater: WallpaperUpdaterWorker
    search: SearchWorker

    def __init__(self) -> None:
        self.wp_updater = WallpaperUpdaterWorker()
        self.wp_updater.start()
        self.search = SearchWorker()
        self.search.start()

    def stop(self):
        self.wp_updater.stop()
        self.search.stop()
