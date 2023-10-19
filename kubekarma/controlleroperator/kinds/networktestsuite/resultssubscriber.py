from datetime import datetime
from typing import List

from kubekarma.controlleroperator.abc.resultspublisher import (
    IResultsSubscriber
)
from kubekarma.controlleroperator.engine.controllerengine import (
    ControllerEngine
)
from kubekarma.controlleroperator.kinds.crdinstancemanager import (
    CRDInstanceManager
)
from kubekarma.controlleroperator.kinds.networktestsuite.resultsdeadline import \
    ResultsDeadlineValidator
from kubekarma.controlleroperator.kinds.statustracker import \
    TestSuiteStatusTracker
from kubekarma.controlleroperator.kinds.types import TestCaseStatusType
from kubekarma.shared.crd.genericcrd import (
    CRDTestExecutionStatus,
    TestCaseStatus
)
from kubekarma.shared.pb2 import controller_pb2

import logging
logger = logging.getLogger(__name__)


class ResultsSubscriber(IResultsSubscriber):

    def __init__(
        self,
        schedule: str,
        crd_manager: CRDInstanceManager,
        controller_engine: ControllerEngine
    ):
        """Initialize the subscriber.

        Args:
            schedule: The schedule of the test suite, in crontab format.
            crd_manager: The manager of the CRD instance.
            controller_engine: The controller engine.
        """
        self.crd_manager = crd_manager
        self.test_suite_status_tracker = TestSuiteStatusTracker()
        self.controller_engine = controller_engine
        self.schedule = schedule
        # The last time the results were received
        self.results_checker = ResultsDeadlineValidator(
            schedule=schedule,
            cron_job_name=crd_manager.crd_data.cron_job_name,
            controller_engine=controller_engine
        )

    def update(
        self,
        results: controller_pb2.ProcessTestSuiteResultsRequest
    ):
        """Receive the results of some the execution task.

        This method is called by the publisher when the results of an
        execution task are available. The results should be interpreted
        and used to set  the status of the CRD.
        """
        # Define the status that are considered as bad
        bad_status = (TestCaseStatus.Failed, TestCaseStatus.Error)

        self.results_checker.mark_results_received(
            datetime.fromisoformat(
                results.started_at_time
            )
        )
        # prepare the patch to be applied to the CRD to report the results
        test_cases: List[TestCaseStatusType] = []
        # The whole test execution status
        whole_test_execution_status = CRDTestExecutionStatus.Succeeding
        failed_test = []

        for result in results.test_case_results:
            test_status = TestCaseStatus.from_pb2_test_status(result.status)
            specific_test_case_status: TestCaseStatusType = {
                # The unique name of the test case, we can consider this
                # as the ID of the test case.
                "name": result.name,
                # The status of the test case.
                "status": test_status.value,
                # The time it took to execute the test case.
                "executionTime": result.execution_duration,
            }
            # Check if the whole test suite should be marked as failing
            if test_status in bad_status:
                whole_test_execution_status = CRDTestExecutionStatus.Failing
                failed_test.append(result.name)
                # If the test case failed due to an error,
                # add the error message to the status.
                if test_status == TestCaseStatus.Error:
                    specific_test_case_status["error"] = result.error_message
            test_cases.append(specific_test_case_status)

        if whole_test_execution_status == CRDTestExecutionStatus.Failing:
            logger.error("Test suite failed: %s", failed_test)
            self.crd_manager.error_event(
                reason="Test suite failed",
                message=f"Failed test: {failed_test}"
            )
        # Create the status object to be applied to the CRD
        status_payload = (
            self.test_suite_status_tracker
            .calculate_current_test_suite_status(
                current_status_reported=whole_test_execution_status,
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

