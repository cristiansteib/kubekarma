import dataclasses

import urllib3

from kubekarma.worker.networksuite.testsuite import logger
from kubekarma.worker.abs.assertion import IAssertion
from kubekarma.worker.abs.exception import AssertionFailure

timeout = urllib3.Timeout(connect=2.0, read=5.0)
http = urllib3.PoolManager(timeout=timeout)


class DestinationHostAssertion(IAssertion):

    @dataclasses.dataclass
    class Config:
        host: str
        port: int
        expect_success: bool

    def __init__(self, config: Config):
        self.config = config

    def _check_host_connectivity(self) -> bool:
        can_connect = False
        try:
            http.request(
                "GET",
                f"{self.config.host}:{self.config.port}"
            )
            can_connect = True
        except Exception:
            logger.exception("Failed to connect to host")
        return can_connect

    def test(self):
        can_connect = self._check_host_connectivity()
        clazz_name = self.__class__.__name__
        if self.config.expect_success:
            if not can_connect:
                raise AssertionFailure(
                    clazz_name,
                    "HTTP failed to connect to host: "
                    f"{self.config.host}:{self.config.port}"
                )
        else:
            if can_connect:
                raise AssertionFailure(
                    clazz_name,
                    f"HTTP connected to host: "
                    f"{self.config.host}:{self.config.port} "
                    f"when it was not expected to"
                )
