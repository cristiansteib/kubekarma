from typing import Dict, Set

from kubekarma.controlleroperator.core.abc.resultspublisher import (
    ITestResultsPublisher,
    IResultsSubscriber
)

import logging

logger = logging.getLogger(__name__)


class ResultsReportPublisher(ITestResultsPublisher):

    def __init__(self):
        self.subscribers: Dict[str, Set[IResultsSubscriber]] = {}

    def add_results_listener(
        self,
        execution_id: str,
        subscriber: IResultsSubscriber
    ):
        """Add a new listener to the results of the execution task."""
        logger.info(
            "Adding listener %s to receive results of execution %s",
            subscriber,
            execution_id
        )
        self.subscribers.setdefault(execution_id, set()).add(subscriber)

    def remove_results_listeners(self, execution_id: str):
        # Delete all abject to avoid memory leaks.
        subscribers_set = self.subscribers.pop(execution_id, {})
        for subscriber in subscribers_set:
            # Catch any exception to avoid breaking the loop causing
            # orphaned subscribers.
            try:
                # Call the hook to delete the subscriber.
                subscriber.on_delete()
            except Exception as e:
                logger.error(
                    "Error calling .on_delete() to subscriber: %s",
                    type(subscriber)
                )
                logger.exception(e)
            finally:
                del subscriber

    def notify_new_results(self, execution_id: str, results):
        for subscriber in self.subscribers.get(execution_id, []):
            try:
                subscriber.update(results)
            except Exception as e:
                logger.exception(e)
