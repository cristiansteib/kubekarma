import threading
from typing import Optional

from kubekarma.controlleroperator.core.resultsreportpublisher import ResultsReportPublisher
from kubekarma.controlleroperator.core.abc.resultspublisher import ITestResultsPublisher

__instance_results_publisher: Optional[ITestResultsPublisher] = None

__lock = threading.Lock()


def get_results_publisher() -> ITestResultsPublisher:
    """Return the result __publisher."""
    with __lock:
        global __instance_results_publisher
        if __instance_results_publisher is None:
            __instance_results_publisher = ResultsReportPublisher()
    return __instance_results_publisher
