import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from worker.networksuite.testsuite import NetworkTestSuite


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
            "kubekarma.worker.nwtestsuite.NetworkTestSuite._run_test"
        ) as _run_test_mock:
            test_suite = NetworkTestSuite(test_config["spec"])
            test_suite.run()
            test_suite._parse_test_case(test_config["spec"]["testCases"][3])
        self.assertEqual(_run_test_mock.call_count, 4)
