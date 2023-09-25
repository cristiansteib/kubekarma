from abc import ABC, abstractmethod


class IResultsSubscriber(ABC):

    @abstractmethod
    def receive_results(self, results: dict):
        """Receive the results of some the execution task."""

    def __hash__(self):
        return hash(id(self))


class IResultsPublisher(ABC):

    @abstractmethod
    def add_results_listener(
        self,
        execution_id: str,
        subscriber: IResultsSubscriber
    ):
        """Add a new listener to the results of the execution task."""

    @abstractmethod
    def remove_all_results_listeners(self, execution_id_token: str):
        """Remove all the listeners for the given execution task."""

    @abstractmethod
    def notify_new_results(self, execution_id, results):
        """Receive the results of some the execution task."""
