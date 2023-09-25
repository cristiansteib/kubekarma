import json
import unittest
from unittest.mock import patch

from kubekarma.dto.executiontask import TestResults
from kubekarma.worker.sender import ControllerCommunication


class ControllerCommunicationTestCase(unittest.TestCase):


    def test_send_results_with_exception(self):
        test_results = TestResults(
            name="test_name",
            passed=False,
            message="Test passed",
        )
        test_results.set_exception(Exception("Test exception"))
        with patch("urllib3.PoolManager.request") as mock_request:
            ControllerCommunication("url").send_results(
                "123",
                [test_results]
            )
            mock_request.assert_called_once_with(
                "POST",
                "url/api/v1/execution-tasks/123",
                body=json.dumps([test_results.to_safe_dict()]),
                headers={
                    "Content-Type": "application/json"
                }
            )