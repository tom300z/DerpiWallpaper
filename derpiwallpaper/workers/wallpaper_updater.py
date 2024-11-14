from  __future__ import annotations
from urllib.parse import urlsplit
import requests
import random
from datetime import datetime, timedelta

from derpiwallpaper.config import CONFIG
from derpiwallpaper.utils import DerpibooruApiError, check_response, get_user_images_folder
from derpiwallpaper.utils.set_wallpaper import set_wallpaper
from derpiwallpaper.workers import WorkerThread, wman


class WallpaperUpdaterWorker(WorkerThread):
    progress = 4
    max_steps = 4
    temporary_error: str | None = None

    _images_url: str = CONFIG.derpibooru_json_api_url + "search/images"
    _next_refresh_time: datetime | None = None

    def __init__(self):
        super().__init__()

    def set_progress(self, progress: int):
        self.progress = progress
        self.update_ui.emit()

    def on_tick(self) -> None:
        # Schedule refresh if auto-refresh is enabled and no refresh is scheduled in the configured interval
        if CONFIG.enable_auto_refresh == True:
            if not self._next_refresh_time or (self._next_refresh_time - datetime.now()).total_seconds() > CONFIG.auto_refresh_interval_seconds:
                self.schedule_refresh(datetime.now() + timedelta(seconds=CONFIG.auto_refresh_interval_seconds))

        if self._next_refresh_time and datetime.now() >= self._next_refresh_time:
            self._refresh_wallpaper()

    def schedule_refresh(self, time: datetime | None, update_ui = True):
        self._next_refresh_time = time
        if update_ui:
            self.update_ui.emit()

    def clear_refresh(self, update_ui = True):
        self._next_refresh_time = None
        if update_ui:
            self.update_ui.emit()


    def get_next_refresh_time(self):
        return self._next_refresh_time

    def _refresh_wallpaper(self) -> None:
        if not wman().search.current_page_count:
            self.temporary_error = "No images found!"
            self.update_ui.emit()
            return
        try:
            START_TIME = datetime.now()
            self.set_progress(0)

            # Set API parameters
            params = {
                "key": CONFIG.derpibooru_json_api_key,  # If you have an API key, insert it here; otherwise, it will use the public anon key
                "q": CONFIG.search_string,
                "per_page": 1,  # Maximum number of results to fetch (max allowed by the API for anon keys is 50)
                "page": random.randint(1, max(1, wman().search.current_page_count))
            }

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
                image_path = CONFIG.wallpaper_folder / f"derpibooru_{random_image['id']}.png"
                with open(image_path, 'wb') as file:
                    file.write(requests.get(image_url).content)
                    self.set_progress(3)


                # Set the downloaded image as the desktop wallpaper (Windows only)
                set_wallpaper(image_path)

                self.temporary_error = None
                print(f"Wallpaper set successfully to a random image matching '{CONFIG.search_string}' from page {params["page"]}/{wman().search.current_page_count}. Runtime: {round((datetime.now()-START_TIME).total_seconds(),1)}s")
        except DerpibooruApiError as e:
            self.temporary_error = f'Derpibooru API Error: {e.error}'
        except requests.ConnectionError as e:
            self.temporary_error = f"Unable to connect to {urlsplit(self._images_url).netloc}."
        finally:
            self.set_progress(4)
            if CONFIG.enable_auto_refresh:
                self.schedule_refresh(datetime.now() + timedelta(seconds=CONFIG.auto_refresh_interval_seconds))
            else:
                self.schedule_refresh(None)
