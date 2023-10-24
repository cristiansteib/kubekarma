import threading

from kubekarma.controlleroperator.core.abc.resultspublisher import \
    ITestResultsPublisher
from kubekarma.controlleroperator.core.resultsreportpublisher import \
    ResultsReportPublisher
from kubekarma.controlleroperator.core.scheduler import SchedulerThread


class ControllerEngine:
    """The heart of the controller"""

    def __init__(self):
        self.scheduler = SchedulerThread()
        self.__publisher = ResultsReportPublisher()

    def is_healthy(self) -> bool:
        """Return True if the controller is healthy, False otherwise."""
        return self.scheduler.is_running()

    def stop(self):
        """Stop the controller"""
        self.scheduler.stop()

    def start(self) -> threading.Thread:
        """Start the controller"""
        self.scheduler.start()
        return self.scheduler

    def get_results_publisher(self) -> ITestResultsPublisher:
        """Get the __publisher of the results of the test suite."""
        return self.__publisher
