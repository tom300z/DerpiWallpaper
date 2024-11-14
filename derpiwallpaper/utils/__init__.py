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
            error = response.json()["error"]
        except:
            error = "Unknown error"
        raise DerpibooruApiError(response.status_code, response.text, error)


    if not all([
        "json" in response.headers.get('Content-Type', ""),
        "total" in response.json(),
        "images" in response.json()
    ]):
        raise DerpibooruApiError(response.status_code, response.text, f"Failed to call derpibooru API. '{response.request.url}' returned invalid body: {response.text}")


# P = ParamSpec("P")  # Parameter specification for the subscriber arguments

# class Observable(Generic[P]):
#     _subscribers: set[Callable[P, Any]]
#     _last_emit_args: tuple[tuple, dict] | None = None

#     def __init__(self) -> None:
#         self._subscribers = set()

#     def sub(self, subscriber: Callable[P, Any], emit_once = False) -> None:
#         self._subscribers.add(subscriber)
#         if emit_once and self._last_emit_args:
#             subscriber(*self._last_emit_args[0], **self._last_emit_args[1])

#     def unsub(self, subscriber: Callable[P, Any]) -> None:
#         self._subscribers.discard(subscriber)

#     def emit(self, *args: P.args, **kwargs: P.kwargs) -> None:
#         self._last_emit_args = (args, kwargs)
#         for sub in self._subscribers:
#             sub(*args, **kwargs)
