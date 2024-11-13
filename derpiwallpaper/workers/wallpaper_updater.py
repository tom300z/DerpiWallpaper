from  __future__ import annotations
from threading import Thread
import requests
import ctypes
import random
import math
import os
from datetime import datetime, timedelta
from PySide6.QtCore import QObject, QThread, Signal, SignalInstance
from tempfile import gettempdir

from derpiwallpaper.config import CONFIG
from derpiwallpaper.utils import DerpibooruApiError, check_response
from derpiwallpaper.utils.set_wallpaper import set_wallpaper
from derpiwallpaper.worker import WorkerThread


class WallpaperUpdaterWorker(WorkerThread):
    progress = 0
    max_steps = 4

    _images_url: str
    _next_refresh_time: datetime | None

    def __init__(self):
        super().__init__()
        self._images_url = CONFIG.derpibooru_json_api_url + "search/images"
        self.schedule_refresh(datetime.now())

    def set_progress(self, progress: int):
        self.progress = progress
        self.update_ui.emit()

    def on_tick(self) -> None:
        if self._next_refresh_time and datetime.now() >= self._next_refresh_time:
            self._refresh_wallpaper()

    def schedule_refresh(self, time: datetime | None, update_ui = True):
        self._next_refresh_time = time
        if update_ui:
            self.update_ui.emit()

    def get_next_refresh_time(self):
        return self._next_refresh_time

    def _refresh_wallpaper(self) -> None:
        try:
            START_TIME = datetime.now()
            self.set_progress(0)

            # Set API parameters
            params = {
                "key": "",  # If you have an API key, insert it here; otherwise, it will use the public anon key
                "q": CONFIG.search_string,
                "per_page": 1  # Maximum number of results to fetch (max allowed by the API for anon keys is 50)
            }

            # Fetch JSON data from Derpibooru for the first page to determine total pages
            response = requests.get(self._images_url, params=params)
            self.set_progress(1)

            # Check if the request was successful and parse json
            check_response(response)
            json_data = response.json()

            # Calculate total pages
            total_pages = math.ceil(json_data['total'] / params["per_page"])

            # Select a random page (ensure it's at least 1, in case totalPages somehow ends up as 0)
            params["page"] = random.randint(1, max(1, total_pages))

            # Fetch JSON data for the random page
            response = requests.get(self._images_url, params=params)
            self.set_progress(2)

            # Proceed with the rest of the script for the random page's images
            check_response(response)
            json_data = response.json()

            # Check if there are any images in the response
            if len(json_data['images']) > 0:
                # Select a random image from the response
                random_image = random.choice(json_data['images'])

                if "view_url" not in random_image:
                    raise RuntimeError(f'Invalid response JSON after fetching images page: image item missing key "view_url". Response body: {response.text}')

                # Construct the direct image URL
                image_url = random_image['view_url']

                # Download the image
                print(gettempdir())
                image_path = os.path.join(gettempdir(), f"derpiwallpaper_{random.randint(1000, 9999)}.png")
                with open(image_path, 'wb') as file:
                    file.write(requests.get(image_url).content)
                    self.set_progress(3)


                # Set the downloaded image as the desktop wallpaper (Windows only)
                set_wallpaper(image_path)

                print(f"Wallpaper set successfully to a random image matching '{CONFIG.search_string}' from page {params["page"]}/{total_pages}. Runtime: {round((datetime.now()-START_TIME).total_seconds(),1)}s")
        except DerpibooruApiError as e:
            pass
        finally:
            self.set_progress(4)
            if CONFIG.enable_auto_refresh:
                self.schedule_refresh(datetime.now() + timedelta(seconds=CONFIG.auto_refresh_interval_seconds))
            else:
                self.schedule_refresh(None)
