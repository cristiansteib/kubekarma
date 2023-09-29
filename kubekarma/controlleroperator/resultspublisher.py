from typing import Dict, Set

from kubekarma.controlleroperator.abc.resultspublisher import (
    IResultsPublisher,
    IResultsSubscriber
)

import logging

logger = logging.getLogger(__name__)


class ResultsPublisher(IResultsPublisher):

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

    def remove_all_results_listeners(self, execution_id_token: str):
        # Delete all abject to avoid memory leaks.
        for subscriber in self.subscribers.pop(execution_id_token, []):
            del subscriber
        # Release the execution_id
        self.subscribers.pop(execution_id_token, None)

    def notify_new_results(self, execution_id: str, results):
        for subscriber in self.subscribers.get(execution_id, []):
            subscriber.receive_results(results)
