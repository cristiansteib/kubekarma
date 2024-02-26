import sched
from datetime import datetime, timedelta
from typing import Optional

from croniter import croniter

from kubekarma.controlleroperator.core.abc.resultspublisher import \
    IResultsSubscriber, T
from kubekarma.controlleroperator.core.controllerengine import \
    ControllerEngine

import logging

from kubekarma.controlleroperator.core.crdinstancemanager import \
    CRDInstanceManager
from kubekarma.shared.loghelper import PrefixFilter

logger = logging.getLogger(__name__)

logger.addFilter(PrefixFilter("ResultsDeadlineValidator: "))


class ResultsDeadlineValidator(IResultsSubscriber):
    """A class to observe if results was received or not at time.

    This class will report an error if the results are not received
    at the expected time.
    """

    def __init__(
            self,
            schedule: str,
            worker_task_id: str,
            controller_engine: ControllerEngine,
            crd_manager: CRDInstanceManager,
            time_execution_estimation: timedelta = timedelta(minutes=1)
    ):
        self.crd_manager = crd_manager
        self.time_execution_estimation = time_execution_estimation
        self.controller_engine = controller_engine
        self.worker_task_id = worker_task_id
        self._croniter = croniter(
            schedule,
            datetime.now()
        )
        self.__expected_time_to_receive_results: Optional[datetime] = None
        self.__last_time_received_results: Optional[datetime] = None
        self.__next_sched_event: Optional[sched.Event] = None
        self.__set_next_time_to_receive_results()

    def mark_results_received(self, received_at: datetime):
        """Mark the results as received."""
        self.__last_time_received_results = received_at

    def __set_next_time_to_receive_results(self):
        self.__expected_time_to_receive_results = (
            self._get_next_time_to_receive_results()
        )
        self.__next_sched_event = self.controller_engine.scheduler.enterabs(
            self.__expected_time_to_receive_results.timestamp(),
            1,
            self.__assert_if_response_was_received
        )
        logger.debug(
            "Next control at %s for %s",
            self.__expected_time_to_receive_results.isoformat(),
            self.worker_task_id,
        )

    def _get_next_time_to_receive_results(self) -> datetime:
        """Set the next time to receive the results."""
        # add some extra time in order to be sure that the results are
        # received after the test suite execution
        return (
            self._croniter.get_next(datetime) +
            self.time_execution_estimation
        )

    def __assert_if_response_was_received(self):
        """Assert if the response was received."""
        # Based on the last time the results were received, we can assert
        # if the response was received or not.
        logger.debug(
            "Running control for %s",
            self.worker_task_id
        )

        if not self.__last_time_received_results:
            logger.error(
                "No response received for task %s",
                self.worker_task_id
            )
            self.crd_manager.error_event(
                "NoResultsReceived",
                "No response received for task"
            )
            self.__set_next_time_to_receive_results()
            return

        # check if happened too much time since the last response
        time_since_last_response = (
            datetime.now() - self.__last_time_received_results
        )
        if time_since_last_response > timedelta(minutes=5):
            logger.warning(
                "Happened too much time since the last response for %s . "
                "Hint: review the time estimation of the test suite.",
                self.worker_task_id
            )
        logger.debug(
            "Successful verification for task %s",
            self.worker_task_id
        )
        self.__last_time_received_results = None
        self.__set_next_time_to_receive_results()

    def update(self, results: T):
        seconds, nanos = results.start_time.seconds, results.start_time.nanos
        self.mark_results_received(
            datetime.fromtimestamp(seconds + nanos / 10 ** 9)
        )

    def on_delete(self):
        # Cancel de scheduled event
        if self.__next_sched_event is not None:
            logger.debug("class id %s", id(self))
            logger.info(
                "Canceling next scheduled control for task %s",
                self.worker_task_id
            )
            self.controller_engine.scheduler.cancel(self.__next_sched_event)
        else:
            logger.debug(
                "No scheduled a next control for task %s",
                self.worker_task_id
            )
