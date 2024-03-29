from copy import deepcopy
from typing import Dict, List

from kubekarma.controlleroperator.core.abc.crdvalidator import ICrdValidator
from kubekarma.controlleroperator.core.testsuite.testsuitekind import \
    TestSuiteKindBase


class InvalidDefinition(Exception):
    ...


class UndefinedCentinel:
    ...


class NetworkTestSuiteCrdValidator(ICrdValidator):

    DEFINED_ASSERTIONS = [
        "testDNSResolution",
        "testIpBlock",
        "testExactDestination",
    ]

    def validate_spec(self, spec: dict) -> List[str]:
        """Validate the spec of the CRD and return a list of errors.

        Rules:
            spec.networkValidations[].name must be unique
                This is required because the test suite name is used to identify each
                test for the results.
        """
        _spec = deepcopy(spec)
        errors = []
        # networkValidations items should only define one assertion type.
        test_cases: List[Dict] = _spec["networkValidations"]
        test_case_names = []
        for index, test_case in enumerate(test_cases):
            # pop element if exists
            test_case.pop("allowedToFail", UndefinedCentinel)
            name = test_case.pop("name", UndefinedCentinel)
            if name is UndefinedCentinel:
                errors.append(
                    f"Missing property spec.networkValidations[{index}].name"
                )
                continue
            test_case_names.append(name)

            if len(test_case.keys()) > 1:
                errors.append(
                    f"networkValidations[{index}] must have exactly one assertion type."
                )
                continue
            assertion_type, assertion_config = test_case.popitem()
            if assertion_type not in self.DEFINED_ASSERTIONS:
                errors.append(
                    f"networkValidations[{index}] has an unsupported assertion type: "
                    f"{assertion_type}"
                )
                continue

        # check for duplicated test names, it must be unique
        duplicates = set(
            [x for x in test_case_names if test_case_names.count(x) > 1]
        )
        if duplicates:
            errors.append(
                f"networkValidations[].name must be unique. (duplicate: {duplicates})"
            )

        return errors


class NetworkTestSuite(TestSuiteKindBase):
    kind = "NetworkTestSuite"
    api_plural = 'networktestsuites'

    def get_crd_validator(self) -> ICrdValidator:
        """Return the controller CRD validator."""
        return NetworkTestSuiteCrdValidator()
