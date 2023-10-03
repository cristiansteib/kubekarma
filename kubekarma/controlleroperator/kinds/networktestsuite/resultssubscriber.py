from datetime import datetime
from typing import List, Optional

from kubekarma.controlleroperator.abc.resultspublisher import IResultsSubscriber
from kubekarma.controlleroperator.kinds.crdinstancemanager import CRDInstanceManager
from kubekarma.controlleroperator.kinds.types import (
    TestCaseStatusType,
    TestSuiteStatusType
)
from kubekarma.shared.crd.genericcrd import CRDTestExecutionStatus, TestCaseStatus
from kubekarma.shared.pb2 import controller_pb2

import logging
logger = logging.getLogger(__name__)


class _TestSuiteStatusTracker:

    def __init__(self):
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
        data = {
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
            "testCases": test_cases
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
        logger.info("current_status: %s", current_status)
        logger.info("latest status: %s", self.latest_status)
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


class ResultsSubscriber(IResultsSubscriber):

    def __init__(self, crd_manager: CRDInstanceManager):
        self.crd_manager = crd_manager
        self.test_suite_status_tracker = _TestSuiteStatusTracker()

    def receive_results(
        self,
        results: controller_pb2.ProcessTestSuiteResultsRequest
    ):
        """Receive the results of some the execution task.

        This method is called by the publisher when the results of an
        execution task are available. The results should be interpreted
        and used to set  the status of the CRD.
        """
        # prepare the patch to be applied to the CRD to report the results
        test_cases: List[TestCaseStatusType] = []
        # The whole test execution status
        test_execution_status = CRDTestExecutionStatus.Succeeding
        for result in results.test_case_results:
            test_status = TestCaseStatus.from_pb2_test_status(result.status)
            test_case_status: TestCaseStatusType = {
                # The unique name of the test case, we can consider this
                # as the ID of the test case.
                "name": result.name,
                # The status of the test case.
                "status": test_status.value,
                # The time it took to execute the test case.
                "executionTime": result.execution_duration,
            }

            # Check if the whole test suite should be marked as failing
            test_execution_status = (
                CRDTestExecutionStatus.Failing
                if test_status in (TestCaseStatus.Failed, TestCaseStatus.Error)
                else test_execution_status
            )
            if test_status == TestCaseStatus.Error:
                test_case_status["error"] = result.error_message
            test_cases.append(test_case_status)

        # Create the status object to be applied to the CRD
        status_payload = (
            self.test_suite_status_tracker
            .calculate_current_test_suite_status(
                current_status_reported=test_execution_status,
                test_cases=test_cases,
                # get datetime from time()
                execution_time=datetime.fromisoformat(
                    results.started_at_time
                )
            )
        )
        self.crd_manager.patch_crd(
            patch={
                "status": status_payload
            }
        )

    def __hash__(self):
        return hash(id(self))
