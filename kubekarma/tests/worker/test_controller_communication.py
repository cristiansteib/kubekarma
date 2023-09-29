import json
import unittest
from unittest.mock import patch

from kubekarma.dto.genericcrd import TestCaseResultItem, TestCaseStatus
from kubekarma.worker.sender import ControllerCommunication


class ControllerCommunicationTestCase(unittest.TestCase):

    def test_send_results_with_exception(self):
        test_results = TestCaseResultItem(
            name="test_name",
            status=TestCaseStatus.Failed,
            executionTime="1s",
            lastExecutionTime="123",
        )
        test_results.set_exception(Exception("Test exception"))
        with patch("urllib3.PoolManager.request") as mock_request:
            mock_request.return_value.status = 200
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