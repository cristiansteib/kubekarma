import threading
from typing import Optional

from kubekarma.controlleroperator.resultspublisher import ResultsPublisher
from kubekarma.controlleroperator.interfaces.resultspublisher import IResultsPublisher

__instance_results_publisher: Optional[IResultsPublisher] = None

__lock = threading.Lock()


def get_results_publisher() -> IResultsPublisher:
    """Return the result publisher."""
    with __lock:
        global __instance_results_publisher
        if __instance_results_publisher is None:
            __instance_results_publisher = ResultsPublisher()
    return __instance_results_publisher


TOOL_NAME = "kubekarma"
