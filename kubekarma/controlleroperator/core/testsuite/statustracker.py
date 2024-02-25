from datetime import datetime
from typing import Optional
import logging

from kubekarma.controlleroperator.core.testsuite.types import TestSuiteStatusType
from kubekarma.shared.crd.genericcrd import CRDTestExecutionStatus, \
    AssertValidationStatus

logger = logging.getLogger(__name__)


class TestSuiteStatusTracker:

    def __init__(self) -> None:
        self.latest_status: Optional[TestSuiteStatusType] = None

    def calculate_current_test_suite_status(
        self,
        current_status_reported: CRDTestExecutionStatus,
        execution_time: datetime,
        test_cases: list
    ) -> TestSuiteStatusType:
        """Return the current status for the CRD instance.

        Based on the current status determined by the results of all test
        cases, calculate all properties values for Status.

        The intention of this is to keep a track over time of the status
        to determinate the times of important events.

        All times are in RFC3339 format.
        """
        execution_time_iso = execution_time.isoformat()
        # count total failed test cases
        failed_test_cases = [
            test_case for test_case in test_cases
            if test_case["status"] in (
                AssertValidationStatus.Failed.value, AssertValidationStatus.Error.value
            )
        ]

        data: TestSuiteStatusType = {
            "lastExecutionTime": execution_time_iso,
            "lastExecutionErrorTime": self.get_last_execution_error_time(
                current_status=current_status_reported,
                current_execution_time=execution_time_iso
            ),
            "lastSucceededTime": self.get_last_succeeded_time(
                current_status=current_status_reported,
                current_execution_time=execution_time_iso
            ),
            "testExecutionStatus": current_status_reported.value,
            "testCases": test_cases,
            "passingCount": f"{len(test_cases) - len(failed_test_cases) } / {len(test_cases)}", # noqa
            "suspended": False
        }
        logger.info("data: %s", data)
        # store the current status
        self.latest_status = data
        return data

    def get_last_succeeded_time(
            self,
            current_status: CRDTestExecutionStatus,
            current_execution_time: str
    ) -> str:
        """Return the last succeeded time."""
        if CRDTestExecutionStatus.Succeeding is current_status:
            return current_execution_time
        if self.latest_status is None:
            return "-"
        return self.latest_status["lastSucceededTime"]

    def get_last_execution_error_time(
        self,
        current_status: CRDTestExecutionStatus,
        current_execution_time: str
    ) -> str:
        """Return the last execution error time.

        This method always returns the LAST execution error time.

        What this means?
            - If an error never happened, return an empty string.
            - if an error happened before but the last execution was
                successful, return the previous error time.
            - If an error happened before and the last execution was
                also an error, return the last execution time.
        """
        if CRDTestExecutionStatus.Failing is current_status:
            return current_execution_time
        if self.latest_status is None:
            return "-"
        return self.latest_status["lastExecutionErrorTime"]
