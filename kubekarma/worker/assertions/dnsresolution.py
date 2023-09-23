import dataclasses
import logging
from typing import Optional

import dns.exception
from dns import resolver

from kubekarma.worker.assertions.abs import IAssertion
from kubekarma.worker.assertions.exception import AssertionFailure

logger = logging.getLogger(__name__)


class DNSResolutionAssertion(IAssertion):

    @dataclasses.dataclass
    class Config:
        host: str
        expect_success: bool
        nameservers: Optional[list] = None

        @classmethod
        def from_dict(cls, d: dict):
            return cls(
                host=d['host'],
                expect_success=d['expectSuccess'],
                nameservers=d.get('nameservers', None)
            )

    def __init__(self, config: Config):
        self.config = config

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            DNSResolutionAssertion.Config.from_dict(d)
        )

    def test(self):
        clazz_name = self.__class__.__name__
        try:
            res = resolver.Resolver()
            if self.config.nameservers:
                res.nameservers = self.config.nameservers
            answers = res.resolve(self.config.host, lifetime=1)
            logger.info(f"DNS resolved host: {self.config.host} to {[a.address for a in answers]}")
            if not self.config.expect_success:
                raise AssertionFailure(
                    clazz_name,
                    f"DNS resolved host: {self.config.host} when it was not expected to"
                )
        except dns.exception.DNSException:
            if self.config.expect_success:
                raise AssertionFailure(
                    clazz_name,
                    f"DNS failed to resolve host: {self.config.host}"
                )
