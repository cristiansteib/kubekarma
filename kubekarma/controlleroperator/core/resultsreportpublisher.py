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
        logger.info("Created new results publisher: %s", id(self))

    def add_results_listener(
        self,
        execution_id: str,
        subscriber: IResultsSubscriber
    ):
        """Add a new listener to the results of the execution task."""
        logger.info(
            "Adding new results listener for execution_id: %s",
            execution_id
        )
        if execution_id not in self.subscribers:
            self.subscribers[execution_id] = set()
        self.subscribers[execution_id].add(subscriber)

    def remove_results_listeners(self, execution_id: str):
        # Delete all abject to avoid memory leaks.
        subscribers_set = self.subscribers.pop(execution_id, {})
        for subscriber in subscribers_set:
            # Send the delete event to the subscriber.
            subscriber.on_delete()
            del subscriber

    def notify_new_results(self, execution_id: str, results):
        for subscriber in self.subscribers.get(execution_id, []):
            subscriber.update(results)
