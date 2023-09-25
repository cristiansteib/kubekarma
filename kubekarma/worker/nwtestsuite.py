import dataclasses
from typing import List

import logging

from kubekarma.worker.assertions.dnsresolution import DNSResolutionAssertion
from kubekarma.worker.assertions.exception import AssertionFailure
from kubekarma.dto.executiontask import TestResults

logger = logging.getLogger(__name__)


class InvalidDefinition(Exception):
    ...


class NetworkPolicyTestSuite:

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
            the configuration follows the format of the NetworkPolicyTestSuite
            CRD located on the file "chart/crds/NetworkPolicyTestSuite.yaml"
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
        keys = set(_test_case.keys())
        if "name" not in keys:
            raise InvalidDefinition("testCases[] items must have a .name")
        test_name = _test_case.pop("name")
        if len(keys) != 2:
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
        clazz = self.DEFINED_ASSERTIONS.get(test_case.assertion_type)
        if clazz is None:
            logger.warning(
                "Assertion type %s is not currently supported.",
                test_case.assertion_type
            )
            return
        assertion = clazz.from_dict(test_case.assertion_config)
        assertion.test()

    def run(self) -> List[TestResults]:
        test_suite_name = self.config_spec["name"]
        logger.info(f"Running test suite {test_suite_name}")
        results = []

        for test in self.config_spec["testCases"]:
            try:
                self._run_test(test)
                results.append(TestResults(
                    name=test["name"],
                    passed=True,
                    message="Test passed",
                    exception=None
                ))
            except AssertionFailure as e:
                test_result = TestResults(
                    name=test["name"],
                    passed=False,
                    message=e.message,
                    exception=None
                )
                test_result.set_exception(e)
                results.append(test_result)
                logger.error(f"Test case {test['name']} failed")
            except Exception as e:
                test_result = TestResults(
                    name=test["name"],
                    passed=False,
                    message=str(e),
                    exception=None
                )
                test_result.set_exception(e)
                results.append(test_result)
                logger.exception(
                    f"Test case {test['name']} failed with unexpected error {e}"
                )
        return results
