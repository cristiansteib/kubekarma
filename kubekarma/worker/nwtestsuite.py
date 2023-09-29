import dataclasses
import time
from typing import List

import logging

from kubekarma.dto.genericcrd import TestCaseResultItem, TestCaseStatus
from kubekarma.worker.assertions.dnsresolution import DNSResolutionAssertion
from kubekarma.worker.assertions.exception import AssertionFailure

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

    def run(self) -> List[TestCaseResultItem]:
        test_suite_name = self.config_spec["name"]
        logger.info(f"Running test suite {test_suite_name}")
        results = []

        for test in self.config_spec["testCases"]:
            start_time = time.perf_counter()
            # Create a partial result item, the rest of the values
            # will be filled by the controller operator.
            test_result = TestCaseResultItem(
                name=test["name"],
                status=TestCaseStatus.Failed,
                executionTime="-",
                lastExecutionTime=str(time.time()),
            )
            try:
                self._run_test(test)
                test_result.status = TestCaseStatus.Succeeded
            except AssertionFailure as e:
                test_result.set_exception(e)
                logger.error(f"Test case {test['name']} failed")
            except NotImplementedError:
                test_result.status = TestCaseStatus.NotImplemented
            except Exception as e:
                test_result.set_exception(e)
                logger.exception(
                    f"Test case %s failed with unexpected error %s",
                    test['name'],
                    e
                )
            finally:
                end_time = time.perf_counter()
                test_result.executionTime = f"{end_time - start_time:0.4f}s"
                results.append(test_result)

        return results
