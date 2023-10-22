import sched
from datetime import datetime, timedelta
from typing import Optional, Type

from croniter import croniter

from kubekarma.controlleroperator.core.abc.resultspublisher import \
    IResultsSubscriber, T
from kubekarma.controlleroperator.core.controllerengine import \
    ControllerEngine

import logging

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
            cron_job_name: str,
            controller_engine: ControllerEngine,
            time_execution_estimation: timedelta = timedelta(minutes=1)
    ):
        self.time_execution_estimation = time_execution_estimation
        self.controller_engine = controller_engine
        self.cron_job_name = cron_job_name
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
        logger.debug(
            "Next scheduled assert for CronJob %s at %s",
            self.cron_job_name,
            self.__expected_time_to_receive_results,
        )
        self.__next_sched_event = self.controller_engine.scheduler.enterabs(
            self.__expected_time_to_receive_results.timestamp(),
            1,
            self.__assert_if_response_was_received
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
            "CronJob <%s> assert if response was received",
            self.cron_job_name
        )
        if not self.__last_time_received_results:
            logger.error(
                "No response received for the CronJob <%s>",
                self.cron_job_name
            )
            # self.crd_manager.error_event(
            #     reason="No response received",
            #     message=(
            #         "The test suite did not send any response. "
            #         "Please check the logs of the test suite."
            #     )
            # )
            #
            self.__set_next_time_to_receive_results()
            return

        # check if happened too much time since the last response
        time_since_last_response = (
            datetime.now() - self.__last_time_received_results
        )
        if time_since_last_response > timedelta(minutes=5):
            logger.debug(
                "happened too much time since the "
                "last response for the CronJob <%s>, time <%s>",
                self.cron_job_name,
                time_since_last_response
            )

        logger.debug(
            "Response received for the CronJob <%s>",
            self.cron_job_name
        )
        self.__last_time_received_results = None
        self.__set_next_time_to_receive_results()

    def update(self, results: T):
        self.mark_results_received(
            datetime.fromisoformat(
                results.started_at_time
            )
        )

    def on_delete(self):
        # Cancel de scheduled event
        if self.__next_sched_event is not None:
            logger.debug(
                "[%s] Canceling next scheduled event %s ...",
                self.cron_job_name,
                self.__next_sched_event.time
            )
            self.controller_engine.scheduler.cancel(self.__next_sched_event)
        else:
            logger.debug(
                "[%s] No next scheduled event to cancel.",
                self.cron_job_name
            )