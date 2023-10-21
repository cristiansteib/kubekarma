import threading

from kubekarma.controlleroperator.core.scheduler import SchedulerThread


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

    def start(self) -> threading.Thread:
        """Start the controller"""
        self.scheduler.start()
        return self.scheduler
