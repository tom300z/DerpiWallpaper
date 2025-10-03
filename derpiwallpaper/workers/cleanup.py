from  __future__ import annotations
from datetime import datetime, timedelta

from derpiwallpaper.config import CLEANUP_INTERVAL, get_conf
from derpiwallpaper.workers import WorkerThread

class WallpaperCleanupWorker(WorkerThread):

    _next_cleanup_time: datetime | None = None

    def on_tick(self) -> None:
        # Schedule cleanup
        if not self._next_cleanup_time or (self._next_cleanup_time - datetime.now()).total_seconds() > CLEANUP_INTERVAL:
            self.schedule_cleanup()

        if self._next_cleanup_time and datetime.now() >= self._next_cleanup_time:
            self._perform_cleanup()

    def schedule_cleanup(self):
        self._next_cleanup_time = datetime.now() + timedelta(seconds=CLEANUP_INTERVAL)

    def _perform_cleanup(self):
        # Scan folder for "derpibooru_" prefixed files
        files = [f for f in get_conf().wallpaper_folder.glob("derpibooru_*") if f.is_file()]

        # Sort files by modification time (most recent last)
        files.sort(key=lambda f: f.stat().st_mtime)

        # Check if we have more files than we want to keep
        if len(files) > get_conf().wallpapers_to_keep:
            files_to_delete = files[:-get_conf().wallpapers_to_keep]  # All but the most recent ones

            for file in files_to_delete:
                file.unlink(missing_ok=True)  # Delete file
            print(f'Cleaned up {len(files_to_delete)} old wallpapers.')