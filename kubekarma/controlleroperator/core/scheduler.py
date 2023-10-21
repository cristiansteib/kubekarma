import sched
import threading
import time
import logging

logger = logging.getLogger(__name__)


class SchedulerThread(threading.Thread):
    """A Daemon thread that runs a scheduler.

    This thread is used to schedule tasks to be executed at a specific time,
    or after a specific delay, without blocking the main thread.


    Considerations:
        If the scheduler is stopped while there are pending events, those
        events will be lost.
    """

    def __init__(self):
        super().__init__()
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.__event = threading.Event()
        # Set this thread as a daemon to avoid waiting for it to finish
        # when the main thread finishes.
        self.daemon = True
        self.__stop = False

    def enterabs(self, a_time, priority, action, argument=(), kwargs={}):
        self.scheduler.enterabs(a_time, priority, action, argument, kwargs)
        self.__event.set()

    def run(self):
        while not self.__stop:
            if self.scheduler.empty():
                self.__event.wait()

            self.scheduler.run(blocking=False)
            time.sleep(1)

        if not self.scheduler.empty():
            logger.info(
                "I'm dying and scheduler is not empty,"
                " pending events (%s)",
                len(self.scheduler.queue)
            )

    def cancel(self, event):
        self.scheduler.cancel(event)

    def stop(self):
        self.__stop = True
        self.__event.set()

    def empty(self):
        return self.scheduler.empty()
