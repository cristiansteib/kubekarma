import threading
from typing import Optional

from kubekarma.controlleroperator.testresultspublisher import TestResultsPublisher
from kubekarma.controlleroperator.abc.resultspublisher import ITestResultsPublisher

__instance_results_publisher: Optional[ITestResultsPublisher] = None

__lock = threading.Lock()


def get_results_publisher() -> ITestResultsPublisher:
    """Return the result publisher."""
    with __lock:
        global __instance_results_publisher
        if __instance_results_publisher is None:
            __instance_results_publisher = TestResultsPublisher()
    return __instance_results_publisher


TOOL_NAME = "kubekarma"
