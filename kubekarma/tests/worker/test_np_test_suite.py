import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from kubekarma.worker.nwtestsuite import NetworkPolicyTestSuite


class NetworkPolicyTestSuiteTest(unittest.TestCase):

    @staticmethod
    def load_yaml() -> dict:
        asset_path = Path(
            "examples/NetworkPolicyTestSuite/test_with_all_asserts.yaml"
        )
        parent_path = __file__.split("/")[:-3]
        f_path = Path("/".join(parent_path)) / asset_path
        with open(f_path) as f:
            return yaml.safe_load(f)

    def test_process_a_spec(self):
        test_config = self.load_yaml()
        with patch(
            "kubekarma.worker.nwtestsuite.NetworkPolicyTestSuite._run_test"
        ) as _run_test_mock:
            test_suite = NetworkPolicyTestSuite(test_config["spec"])
            test_suite.run()
        self.assertEqual(_run_test_mock.call_count, 4)
