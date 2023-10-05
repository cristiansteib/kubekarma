from typing import NotRequired, TypedDict

from kubekarma.worker.abs.assertion import IAssertion

import socket

import logging


logger = logging.getLogger(__name__)


class ExactDestinationAssertionSpecTypeDict(TypedDict):
    destinationIP: str
    port: int
    expectSuccess: bool
    protocol: str


class ExactDestinationAssertion(IAssertion):

    def __init__(self, spec: ExactDestinationAssertionSpecTypeDict):
        self.spec = spec

    @classmethod
    def validate_spec(cls, d: dict):
        current_keys = set(d.keys())
        # exclude the optional keys
        expected_keys = set(
            ExactDestinationAssertionSpecTypeDict.__annotations__.keys()
        )
        if current_keys != expected_keys:
            raise Exception(
                f"Invalid spec for {cls.__name__}. "
                f"Expected keys: {expected_keys}. "
                f"Current keys: {current_keys}"
            )

    @classmethod
    def from_dict(cls, d: dict) -> 'ExactDestinationAssertion':
        if "protocol" not in d:
            d["protocol"] = "tcp"
        else:
            d["protocol"] = d["protocol"].lower()
        cls.validate_spec(d)
        return cls(d)

    @staticmethod
    def _connect(host: str, port: int, protocol: str) -> bool:
        """Return True if the connection was successful, False otherwise."""
        is_tcp = protocol == "tcp"
        s = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM if is_tcp else socket.SOCK_DGRAM
        )
        s.settimeout(2)
        results = s.connect_ex((host, port))
        s.close()
        return results == 0

    def test(self):
        # test connection to the specified destination
        host = self.spec["destinationIP"]
        port = self.spec["port"]
        expect_success: bool = self.spec["expectSuccess"]

        expected_failure_msg = (
            f"TCP connection to host {host}:{port} was successful "
            f"when it was expected to fail"
        )
        expected_success_msg = (
            f"TCP connection to host {host}:{port} was unsuccessful "
            f"when it was expected to succeed"
        )
        try:
            connected = self._connect(host, port, self.spec["protocol"])
            if not expect_success and connected:
                self.raise_assertion_failure(expected_failure_msg)
            elif expect_success and not connected:
                self.raise_assertion_failure(expected_success_msg)
        except socket.timeout:
            if expect_success:
                self.raise_assertion_failure(expected_success_msg)
