from typing import List, Optional

from kubekarma.controlleroperator.abc.resultspublisher import IResultsSubscriber
from kubekarma.controlleroperator.kinds.crdinstancemanager import CRDInstanceManager
from kubekarma.controlleroperator.kinds.types import (
    TestCaseStatusType,
    TestSuiteStatusType
)
from kubekarma.shared.crd.genericcrd import CRDTestExecutionStatus, TestCaseStatus
from kubekarma.shared.pb2 import controller_pb2


class _TestSuiteStatusTracker:

    def __init__(self):
        self.latest_status: Optional[TestSuiteStatusType] = None

    def calculate_current_test_suite_status(
            self,
            current_status_reported: TestCaseStatus,
            test_cases: list
    ) -> TestSuiteStatusType:
        """Return the current status for the CRD instance.

        Based on the current status determined by the results of all test
        cases, calculate all properties values for Status.

        The intention of this is to keep a track over time of the status
        to determinate the times of important events.
        """
        # TODO: track last time status changed
        return {
            "lastExecutionTime": self.get_last_execution_time(),
            "lastExecutionErrorTime": self.get_last_execution_error_time(),
            "lastSucceededTime": self.get_last_succeeded_time(),
            "testExecutionStatus": current_status_reported.value,
            "testCases": test_cases
        }

    def get_last_execution_time(self) -> str:
        """Return the last execution time."""
        return ""

    def get_last_succeeded_time(self) -> str:
        """"""

    def get_last_execution_error_time(self) -> str:
        """Return the last execution error time.

        This method always returns the LAST execution error time.

        What this means?
            - If an error never happened, return an empty string.
            - if an error happened before but the last execution was
                successful, return the previous error time.
            - If an error happened before and the last execution was
                also an error, return the last execution time.
        """
        return ""


class ResultsSubscriber(IResultsSubscriber):

    def __init__(self, crd_manager: CRDInstanceManager):
        self.crd_manager = crd_manager
        self.test_suite_status_tracker = _TestSuiteStatusTracker()

    @staticmethod
    def get_status(status: controller_pb2.TestStatus) -> TestCaseStatus:
        """Return the test case status defined by the CRD."""
        # This class could be agnostic of the specific kubekarma CRD
        if status == controller_pb2.TestStatus.SUCCEEDED:
            return TestCaseStatus.Succeeded
        elif status == controller_pb2.TestStatus.FAILED:
            return TestCaseStatus.Failed
        elif status == controller_pb2.TestStatus.NOTIMPLEMENTED:
            return TestCaseStatus.NotImplemented
        elif status == controller_pb2.TestStatus.ERROR:
            return TestCaseStatus.Error
        else:
            raise Exception(f"Unknown status: {status}")

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
            test_status = self.get_status(result.status)
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

        calculated_status = (
            self.test_suite_status_tracker
            .calculate_current_test_suite_status(
                current_status_reported=test_execution_status,
                test_cases=test_cases
            )
        )
        self.crd_manager.patch_crd(
            patch={
                "status": calculated_status
            }
        )

    def __hash__(self):
        return hash(id(self))
