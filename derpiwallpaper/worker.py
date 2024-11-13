from threading import Event, Thread
from time import sleep
from PySide6.QtCore import Signal, SignalInstance, QObject


class WorkerThread(Thread, QObject):
    stop_event: Event

    update_ui: SignalInstance = Signal() # type: ignore

    def __init__(self) -> None:
        Thread.__init__(self)
        QObject.__init__(self)

        self.stop_event = Event()

    def on_tick(self):
        ...


    def run(self) -> None:
        while not self.stop_event.is_set():
            self.on_tick()
            sleep(0.1)

    def stop(self, join = True):
        self.stop_event.set()

        if join:
            self.join()