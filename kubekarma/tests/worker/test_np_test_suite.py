import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from kubekarma.worker.networksuite.testsuite import NetworkKubekarmaTestSuite


class NetworkTestTestCase(unittest.TestCase):

    @staticmethod
    def load_yaml() -> dict:
        asset_path = Path(
            "examples/NetworkTestSuite/test_with_all_asserts.yaml"
        )
        parent_path = __file__.split("/")[:-4]
        f_path = Path("/".join(parent_path)) / asset_path
        with open(f_path) as f:
            return yaml.safe_load(f)

    def test_process_a_spec(self):
        test_config = self.load_yaml()
        with patch(
            "kubekarma.worker.networksuite.dnsresolutionassertion.DNSResolutionAssertion.test"
        ) as _run_test_mock:
            test_suite = NetworkKubekarmaTestSuite(test_config["spec"])
            self.assertEqual(
                4, len(test_suite.test_cases),
            )
            test_case = test_suite._parse_test_case(test_config["spec"]["networkValidations"][3])
            results = test_suite.execute_test(test_case)
        self.assertEqual(_run_test_mock.call_count, 1)
