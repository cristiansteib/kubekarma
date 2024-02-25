
from typing import List

import logging


from kubekarma.worker.abs.exception import InvalidDefinition
from kubekarma.worker.abs.ikubekarmatestsuite import IKubekarmaTest, \
    IKubekarmaTestSuite
from kubekarma.worker.networksuite.dnsresolutionassertion import DNSResolutionAssertion
from kubekarma.worker.networksuite.exactdestionationassertion import \
    ExactDestinationAssertion

logger = logging.getLogger(__name__)


class NetworkKubekarmaTestSuite(IKubekarmaTestSuite):

    kind = "NetworkTestSuite"

    DEFINED_ASSERTIONS = {
        "testDNSResolution": DNSResolutionAssertion,
        "testIpBlock": None,
        "testExactDestination": ExactDestinationAssertion,
    }

    class NetworkKubekarmaTest(IKubekarmaTest):

        def __init__(self, name, assertion_type, assertion_config):
            self._name = name
            self.assertion_type = assertion_type
            self.assertion_config = assertion_config

        @property
        def name(self) -> str:
            return self._name

    def __init__(self, config_spec: dict):
        """
        Args:
            config_spec (dict): The configuration for the test suite.
            the configuration follows the format of the NetworkKubarmaTestSuite
            CRD located on the file "chart/crds/NetworkKubarmaTestSuite.yaml"
            config_spec examples:
                {
                  "name": "test-suite-1",
                  "networkValidations": [
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
        self._name = config_spec["name"]
        self._test_cases = list(
            map(self._parse_test_case, config_spec["networkValidations"])
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def test_cases(self) -> List[IKubekarmaTest]:
        return self._test_cases

    def execute_test(self, test_case: NetworkKubekarmaTest):
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

    def _parse_test_case(self, test_case_spec: dict) -> NetworkKubekarmaTest:
        """Parse the config spec to retrieve the TestCase information.

        This method also perform validations on the test case spec.
        """
        _test_case = test_case_spec.copy()
        # TODO: improve this method
        keys = set(_test_case.keys())
        if "name" not in keys:
            raise InvalidDefinition("networkValidations[] items must have a .name")
        test_name = _test_case.pop("name")
        # remove this value to only keep the assertion type
        _test_case.pop("allowedToFail", None)
        keys = set(_test_case.keys())
        if len(keys) != 1:
            raise InvalidDefinition(
                f"networkValidations[{test_name}] must have exactly one assertion type."
            )
        assertion_type, assertion_config = _test_case.popitem()
        if assertion_type not in self.DEFINED_ASSERTIONS:
            raise InvalidDefinition(
                f"networkValidations <{test_name}> has an unsupported assertion type: "
                f"<{assertion_type}>"
            )

        return self.NetworkKubekarmaTest(
            test_name, assertion_type, assertion_config
        )
