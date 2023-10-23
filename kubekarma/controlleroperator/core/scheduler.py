import sched
import threading
import time
import logging

logger = logging.getLogger(__name__)


class SchedulerThread(threading.Thread):
    """A Daemon thread that runs a __scheduler.

    This thread is used to schedule tasks to be executed at a specific time,
    or after a specific delay, without blocking the main thread.


    Considerations:
        If the __scheduler is stopped while there are pending events, those
        events will be lost.
    """

    def __init__(self):
        super().__init__()
        self.__scheduler = sched.scheduler(time.time, time.sleep)
        self.__event = threading.Event()
        # Set this thread as a daemon to avoid waiting for it to finish
        # when the main thread finishes.
        self.daemon = True
        self.__stop = False

    def enterabs(
            self,
            a_time,
            priority,
            action,
            argument=(),
            kwargs={}
    ) -> sched.Event:
        event = self.__scheduler.enterabs(
            a_time,
            priority,
            action,
            argument,
            kwargs
        )
        self.__event.set()
        return event

    def run(self):
        logger.info("Starting __scheduler thread.")
        while not self.__stop:
            if self.__scheduler.empty():
                self.__event.wait()

            self.__scheduler.run(blocking=False)
            time.sleep(1)

        if not self.__scheduler.empty():
            logger.info(
                "I'm dying and __scheduler is not empty,"
                " pending events (%s)",
                len(self.__scheduler.queue)
            )

    def cancel(self, event):
        self.__scheduler.cancel(event)

    def stop(self):
        self.__stop = True
        self.__event.set()

    def empty(self):
        return self.__scheduler.empty()
