import abc
from typing import List

from kubernetes import client
from kubernetes.client import V1CronJob

from kubekarma.controlleroperator.config import Config
from kubekarma.controlleroperator.core.abc.resultspublisher import \
    IResultsSubscriber
from kubekarma.controlleroperator.core.crdinstancemanager import CRD, \
    CRDInstanceManager


class ITestSuiteKind(abc.ABC):

    @property
    @abc.abstractmethod
    def api_client(self) -> client.ApiClient:
        """Get the api_client to connect to the Kubernetes API."""

    @abc.abstractmethod
    def get_crd_for_creation(
        self,
        namespace: str,
        metadata_name: str,
        api_plural: str
    ) -> CRD:
        """Return a CRD instance prepared for the creation lifecycle event."""

    @abc.abstractmethod
    def initialize_results_listeners(
        self,
        crd: CRD,
        spec: dict,
        crd_manager: CRDInstanceManager
    ) -> List[IResultsSubscriber]:
        """Listen for the results of the execution task."""

    @staticmethod
    @abc.abstractmethod
    def generate_cron_job(
        kind: str,
        crd: CRD,
        schedule: str,
        task_execution_config: dict,
        the_config: Config,
    ) -> V1CronJob:
        """Generate the cronjob that will execute the test suite."""

    @abc.abstractmethod
    def remove_all_listeners(self, worker_task_id: str):
        """Remove all the listeners."""

    @abc.abstractmethod
    def suspend_operations(self, crd_manager: CRDInstanceManager):
        """Suspend the operations for the CRD instance."""

    @abc.abstractmethod
    def resume_operations(self, crd_manager: CRDInstanceManager, spec: dict):
        """Resume the operations for the CRD instance."""
