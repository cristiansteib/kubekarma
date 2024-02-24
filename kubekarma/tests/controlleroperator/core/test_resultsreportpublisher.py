import unittest
from unittest.mock import Mock

from kubekarma.controlleroperator.core.abc.resultspublisher import \
    IResultsSubscriber
from kubekarma.controlleroperator.core.resultsreportpublisher import \
    ResultsReportPublisher


class ResultsReportPublisherTest(unittest.TestCase):

    def test_publisher_behaviour(self):
        publisher = ResultsReportPublisher()
        susb_1 = Mock(spec=IResultsSubscriber)
        susb_2 = Mock(spec=IResultsSubscriber)
        execution_id = "execution_id"
        publisher.add_results_listener(
            execution_id,
            subscriber=susb_1
        )
        publisher.add_results_listener(
            execution_id,
            subscriber=susb_2
        )

        publisher.notify_new_results(
            execution_id,
            results=None
        )
        susb_1.update.assert_called_once_with(None)
        susb_2.update.assert_called_once_with(None)

        publisher.remove_results_listeners(execution_id)

        susb_1.on_delete.assert_called_once_with()
        susb_2.on_delete.assert_called_once_with()

        # Validate that the subscribers are removed and not called anymore
        publisher.notify_new_results(
            execution_id,
            results=True
        )
        susb_1.update.assert_called_once_with(None)
        susb_2.update.assert_called_once_with(None)
