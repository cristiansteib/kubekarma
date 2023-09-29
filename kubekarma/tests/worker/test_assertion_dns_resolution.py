import unittest

from kubekarma.worker.assertions.dnsresolution import DNSResolutionAssertion
from kubekarma.worker.assertions.exception import AssertionFailure


class DnsResolutionAssertionTest(unittest.TestCase):

    def test_with_expected_failure(self):
        config = {
            "nameservers": ["0.0.1.0"],
            "host": "google.com",
            "expectSuccess": False
        }
        assertion = DNSResolutionAssertion.from_dict(config)
        assertion.test()

    def test_with_unexpected_failure(self):
        config = {
            "nameservers": ["0.0.1.0"],
            "host": "google.com",
            "expectSuccess": True
        }
        assertion = DNSResolutionAssertion.from_dict(config)
        with self.assertRaises(AssertionFailure):
            assertion.test()

    def test_success_case(self):
        config = {
            "nameservers": [],
            "host": "google.com",
            "expectSuccess": True
        }
        assertion = DNSResolutionAssertion.from_dict(config)
        assertion.test()

    def test_success_when_is_not_excpected(self):
        config = {
            "nameservers": [],
            "host": "google.com",
            "expectSuccess": False
        }
        assertion = DNSResolutionAssertion.from_dict(config)
        with self.assertRaises(AssertionFailure):
            assertion.test()
