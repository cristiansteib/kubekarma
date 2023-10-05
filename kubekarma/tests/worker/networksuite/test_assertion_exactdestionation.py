import contextlib
import unittest
from unittest.mock import patch

from kubekarma.worker.abs.exception import AssertionFailure
from kubekarma.worker.networksuite.exactdestionationassertion import \
    ExactDestinationAssertion, ExactDestinationAssertionSpecTypeDict


class ExactDestinationAssertionTest(unittest.TestCase):

    @staticmethod
    def _get_config(**kwargs) -> ExactDestinationAssertionSpecTypeDict:
        base = {
            "port": 53,
            "destinationIP": "127.0.0.1",
            "expectSuccess": True,
            "protocol": "udp"
        }
        # merge the base with the kwargs
        base.update(kwargs)
        return base

    @staticmethod
    @contextlib.contextmanager
    def _patched_connect(succeed: bool):
        with patch(
            "kubekarma.worker.networksuite.exactdestionationassertion"
            ".ExactDestinationAssertion._connect"
        ) as mock_connect:
            mock_connect.return_value = succeed
            yield

    def test_expected_success_when_connection_fails(self):
        spec = self._get_config(expectSuccess=True)
        assertion = ExactDestinationAssertion.from_dict(spec)
        with self._patched_connect(False):
            with self.assertRaises(AssertionFailure):
                assertion.test()

    def test_expected_success_when_connection_is_ok(self):
        spec = self._get_config(expectSuccess=True)
        assertion = ExactDestinationAssertion.from_dict(spec)
        with self._patched_connect(True):
            assertion.test()

    def test_expected_failure_when_connection_fails(self):
        spec = self._get_config(expectSuccess=False)
        assertion = ExactDestinationAssertion.from_dict(spec)
        with self._patched_connect(False):
            assertion.test()

    def test_expected_failure_when_connection_is_ok(self):
        spec = self._get_config(expectSuccess=False)
        assertion = ExactDestinationAssertion.from_dict(spec)
        with self._patched_connect(True):
            with self.assertRaises(AssertionFailure):
                assertion.test()
