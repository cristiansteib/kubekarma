import json
import logging
from typing import List

import urllib3

from kubekarma.dto.genericcrd import TestCaseResultItem


class ControllerNotAvailable(Exception):
    ...


logger = logging.getLogger(__name__)


class ControllerCommunication:

    def __init__(self, controller_url: str):
        self.controller_url = controller_url
        timeout = urllib3.Timeout(connect=2.0, read=5.0)
        self.http = urllib3.PoolManager(timeout=timeout)

    def ping_controller(self) -> bool:
        try:
            response = self.http.request(
                "GET",
                f"{self.controller_url}/healthz",
            )
            logger.info(f"Controller /healthz response: {response.status}")
            return response.status == 200
        except Exception as error:
            raise ControllerNotAvailable() from error

    def send_results(
            self,
            task_identifier: str,
            results: List[TestCaseResultItem]
    ):
        """Send the results of a task execution to the controller."""
        url = f"{self.controller_url}/api/v1/execution-tasks/{task_identifier}"
        payload = [result.to_safe_dict() for result in results]
        body = json.dumps(payload)
        try:
            response = self.http.request(
                "POST",
                url,
                body=body,
                headers={
                    "Content-Type": "application/json"
                }
            )
            if response.status != 200:
                raise ControllerNotAvailable(
                    f"Failed to send results to controller: {response.status}"
                )
        except Exception as error:
            raise ControllerNotAvailable() from error
