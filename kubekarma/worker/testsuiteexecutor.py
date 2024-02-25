import time
from typing import List

from kubekarma.grpcgen.collectors.v1alpha.controller_pb2 import (
    ValidationResult,
    ExecutionResultRequest
)
from google.protobuf.timestamp_pb2 import Timestamp

from kubekarma.worker import utils
from kubekarma.worker.abs.exception import AssertionFailure
from kubekarma.worker.abs.ikubekarmatestsuite import IKubekarmaTest, \
    IKubekarmaTestSuite
import logging

logger = logging.getLogger(__name__)


def gen_timestamp(a_time: float) -> Timestamp:
    seconds, micros = divmod(a_time, 10 ** 6)
    return Timestamp(
        seconds=int(seconds),
        nanos=int(micros * 10 ** 3)
    )


class TestSuiteExecutor:

    def __init__(self, kubekarma_test_suite: IKubekarmaTestSuite, token: str):
        self.kubekarma_test_suite = kubekarma_test_suite
        self.token = token

    def run_test(self, test_case: IKubekarmaTest) -> ValidationResult:
        start_time = time.perf_counter()
        status_type = ValidationResult.Status
        seconds, micros = divmod(time.time(), 10 ** 6)
        partial_test_result = {
            "name": test_case.name,
            "status": ValidationResult.Status.FAILED,
            "start_time": Timestamp(
                seconds=int(seconds),
                nanos=int(micros * 10 ** 3)
            )
        }
        try:
            self.kubekarma_test_suite.execute_test(test_case)
            partial_test_result["status"] = status_type.SUCCEEDED
        except AssertionFailure:
            logger.info("[%s] ... FAILED", test_case.name)
        except NotImplementedError:
            partial_test_result["status"] = status_type.NOTIMPLEMENTED
            logger.info("[%s] ... SKIPPED", test_case.name)
        except Exception as e:
            logger.exception(
                "[%s] ... ERROR", test_case.name
            )
            partial_test_result["status"] = status_type.ERROR
            partial_test_result["error_message"] = utils.stringify_exception(e)
        finally:
            partial_test_result["execution_time"] = gen_timestamp(
                time.perf_counter() - start_time
            )
            return ValidationResult(**partial_test_result)

    def execute(self) -> ExecutionResultRequest:
        logger.info(
            "[%s] Running test suite",
            self.kubekarma_test_suite.name
        )
        start_time = gen_timestamp(time.perf_counter())
        results: List[ValidationResult] = []
        for test_case in self.kubekarma_test_suite.test_cases:
            results.append(
                self.run_test(test_case)
            )
        return ExecutionResultRequest(
            name=self.kubekarma_test_suite.name,
            validation_results=results,
            start_time=start_time,
            token=self.token
        )
