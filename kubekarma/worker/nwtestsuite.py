import dataclasses
import time
from typing import List

import logging

from kubekarma.worker.assertions.dnsresolution import DNSResolutionAssertion
from kubekarma.worker.assertions.exception import AssertionFailure
from kubekarma.shared.pb2.controller_pb2 import TestCaseResult
from kubekarma.shared.pb2 import controller_pb2

logger = logging.getLogger(__name__)


class InvalidDefinition(Exception):
    ...


class NetworkTestSuite:

    @dataclasses.dataclass
    class TestCase:
        name: str
        assertion_type: str
        assertion_config: dict

    DEFINED_ASSERTIONS = {
        "testDNSResolution": DNSResolutionAssertion,
        "testIpBlock": None,
        "testExactDestination": None,
    }

    def __init__(self, config_spec: dict):
        """
        Args:
            config_spec (dict): The configuration for the test suite.
            the configuration follows the format of the NetworkTestSuite
            CRD located on the file "chart/crds/NetworkTestSuite.yaml"
            config_spec examples:
                {
                  "name": "test-suite-1",
                  "testCases": [
                    { "testExactDestination":
                        {
                            "destinationIp": "1.1.1.1",
                            "port": 80,
                            "expectSuccess": False
                        }
                    }
                ]
        """
        self.config_spec = config_spec

    def _parse_test_case(self, test_case_spec: dict) -> TestCase:
        """Parse the config spec to retrieve the TestCase information.

        This method also perform validations on the test case spec.
        """
        _test_case = test_case_spec.copy()
        # TODO: improve this method
        keys = set(_test_case.keys())
        if "name" not in keys:
            raise InvalidDefinition("testCases[] items must have a .name")
        test_name = _test_case.pop("name")
        # remove this value to only keep the assertion type
        _test_case.pop("allowedToFail", None)
        keys = set(_test_case.keys())
        if len(keys) != 1:
            raise InvalidDefinition(
                f"testCases[{test_name}] must have exactly one assertion type."
            )
        assertion_type, assertion_config = _test_case.popitem()
        if assertion_type not in self.DEFINED_ASSERTIONS:
            raise InvalidDefinition(
                f"testCases <{test_name}> has an unsupported assertion type: "
                f"<{assertion_type}>"
            )
        return self.TestCase(
            name=test_name,
            assertion_type=assertion_type,
            assertion_config=assertion_config
        )

    def _run_test(self, test_case_spec: dict):
        test_case = self._parse_test_case(test_case_spec)
        clazz = self.DEFINED_ASSERTIONS.get(
            test_case.assertion_type
        )
        if clazz is None:
            raise NotImplementedError(
                f"Assertion type {test_case.assertion_type} "
                "is not currently supported."
            )
        assertion = clazz.from_dict(test_case.assertion_config)
        assertion.test()

    @staticmethod
    def __stringify_exception(e: Exception) -> str:
        exception_type = type(e).__name__
        message = str(e)
        a_traceback = e.__traceback__
        file_name = a_traceback.tb_frame.f_code.co_filename if a_traceback else None
        line_number = a_traceback.tb_lineno if a_traceback else None
        function_name = a_traceback.tb_frame.f_code.co_name if a_traceback else None
        return (
            f"{exception_type}: {message}\n"
            f"  File \"{file_name}\", line {line_number}, in {function_name}"
        )

    def run(self) -> List[TestCaseResult]:
        test_suite_name = self.config_spec["name"]
        logger.info(f"Running test suite {test_suite_name}")
        results = []

        for test in self.config_spec["testCases"]:
            start_time = time.perf_counter()
            # Create a partial result item, the rest of the values
            # will be filled by the controller operator.
            test_result = TestCaseResult(
                name=test["name"],
                status=controller_pb2.TestStatus.FAILED,
                execution_duration="-",
                execution_start_time=str(time.time()),
            )
            try:
                self._run_test(test)
                test_result.status = controller_pb2.TestStatus.SUCCEEDED
            except AssertionFailure as e:
                logger.error(f"Test case {test['name']} failed")
            except NotImplementedError:
                test_result.status = controller_pb2.TestStatus.NOTIMPLEMENTED
            except Exception as e:
                logger.exception(
                    f"Test case %s failed with unexpected error %s",
                    test['name'],
                    e
                )
                test_result.status = controller_pb2.TestStatus.ERROR
                test_result.error_message = self.__stringify_exception(e)
            finally:
                end_time = time.perf_counter()
                test_result.execution_duration = (
                    f"{end_time - start_time:0.4f}s"
                )
                results.append(test_result)

        return results
