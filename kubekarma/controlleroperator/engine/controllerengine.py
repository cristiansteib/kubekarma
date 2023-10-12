import threading

from kubekarma.controlleroperator.engine.scheduler import SchedulerThread


class ControllerEngine:
    """The heart of the controller"""

    def __init__(self):
        self.scheduler = SchedulerThread()

    def is_healthy(self) -> bool:
        """Return True if the controller is healthy, False otherwise."""
        return self.scheduler.isAlive()

    def stop(self):
        """Stop the controller"""
        self.scheduler.stop()

    def _verify_last_report_status(self):
        """Check the last report status of each object."""
        self.scheduler.enterabs(5, 1, self._verify_last_report_status)

    def start(self) -> threading.Thread:
        """Start the controller"""
        self.scheduler.start()
        return self.scheduler
