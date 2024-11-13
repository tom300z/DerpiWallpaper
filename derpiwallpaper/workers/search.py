from  __future__ import annotations
from threading import Thread
import requests
import ctypes
import random
import math
import os
from datetime import datetime, timedelta
from PySide6.QtCore import QObject, QThread, Signal, SignalInstance

from derpiwallpaper.config import CONFIG
from derpiwallpaper.utils import DerpibooruApiError, check_response, wait_until
from derpiwallpaper.worker import WorkerThread

class SearchWorker(WorkerThread):

    _images_url: str
    _current_search_string: str | None = None
    current_result_count: int = 0
    current_page_count: int = 0
    current_error_msg: str | None = None
    _last_request_time: datetime

    def __init__(self):
        super().__init__()
        self._images_url = CONFIG.derpibooru_json_api_url + "search/images"
        self._last_request_time = datetime.now()

    def on_tick(self) -> None:
        if CONFIG.search_string != self._current_search_string:
            self._refresh_results()

    def _refresh_results(self) -> None:
        # Wait until 1s after the last request to avoid hitting rate limits
        wait_until(self._last_request_time+timedelta(seconds=1))

        try:
            # Set API parameters
            params = {
                "key": CONFIG.derpibooru_json_api_key,  # If you have an API key, insert it here; otherwise, it will use the public anon key
                "q": CONFIG.search_string,
                "per_page": 1  # Maximum number of results to fetch (max allowed by the API for anon keys is 50)
            }

            # Fetch JSON data from Derpibooru for the first page to determine total pages
            response = requests.get(self._images_url, params=params)
            self._last_request_time = datetime.now()
            self._current_search_string = params["q"]

            # Check if the request was successful and parse json
            check_response(response)


            json_data = response.json()

            # Update results & pages
            self.current_result_count = json_data['total']
            self.current_page_count = math.ceil(json_data['total'] / params["per_page"])
            self.current_error_msg = None

        except DerpibooruApiError as e:
            self.current_error_msg = e.error

        finally:
            self.update_ui.emit()

