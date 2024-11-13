from datetime import datetime
from time import sleep

import requests

def wait_until(target_time: datetime):
    now = datetime.now()
    if target_time > now:
        wait_seconds = (target_time - now).total_seconds()
        print(f"Waiting {wait_seconds:.2f} seconds until {target_time}")
        sleep(wait_seconds)

class DerpibooruApiError(RuntimeError):
    code: int
    body: str
    error: str
    def __init__(self, code: int, body: str, error: str) -> None:
        self.code = code
        self.body = body
        self.error = error

def check_response(response: requests.Response):
    if response.status_code != 200:
        try:
            json = response.json()
        except:
            json = {}
        if "error" in response.json():
            raise DerpibooruApiError(response.status_code, response.text, json["error"])

        raise RuntimeError(f"Failed to call derpibooru API. '{response.request.url}' returned status code: {response.status_code}")

    if not all([
        "json" in response.headers.get('Content-Type', ""),
        "total" in response.json(),
        "images" in response.json()
    ]):
        raise RuntimeError(f"Failed to call derpibooru API. '{response.request.url}' returned invalid body: {response.text}")
