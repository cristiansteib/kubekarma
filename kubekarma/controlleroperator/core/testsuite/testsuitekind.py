"""
A TestSuite Kind is composed of:

::: A Handlers for lifecycle events :::

1) A creation handler
2) A deletion handler
3) A update handler
4) A resume handler
5) A pause handler

::: Components :::

1)[*] A Deadline validator: to check if the results are received in time.
2)[*] A results subscriber: to change the status of the CRD
3)[*] A CRD manager: to manipulate CRD object (status, metadata, ...)


[*] The component must react to the lifecycle events of the CRD.

::: Helpers :::

1) Notifier: to notify the results to persons or systems.



~~~ Actions taken by the operator ~~~

- Attach to notifications strategies to report the results of the tests.
- Create a cronjob to execute the tests defined by the user.
- React to the cronjob results to update the status of the CRD.
- Report malfunctioning of the cronjob.
  - Creation error
  - Execution error
  - A deadline is reached and the results are not received.
"""
import abc
import contextvars
from hashlib import sha1
from typing import Optional, Type

from kopf import Body
from kubernetes import client
from kubernetes.client import V1CronJob

from kubekarma.controlleroperator.core.abc.resultspublisher import \
    IResultsSubscriber
from kubekarma.controlleroperator.config import Config
from kubekarma.controlleroperator.core.abc.crdvalidator import ICrdValidator
from kubekarma.controlleroperator.core.abc.testsuitekind import ITestSuiteKind
from kubekarma.controlleroperator.core.controllerengine import \
    ControllerEngine
from kubekarma.controlleroperator.core.crdinstancemanager import CRD, \
    CRDInstanceManager
from kubekarma.controlleroperator.core.cronjob import CronJobHelper

import logging

from kubekarma.controlleroperator.core.testsuite.resultsdeadline import \
    ResultsDeadlineValidator
from kubekarma.controlleroperator.core.testsuite.resultsreportsubscriber import \
    ResultsReportSubscriber

logger = logging.getLogger(__name__)


class TestSuiteKindBase(ITestSuiteKind):
    """This class provides the base functionality for a TestSuiteKind.

    A TestSuiteKind is a kind of CRD that is used to define a test suite
    and this class provides the base functionality to handle the lifecycle
    events of the CRD and to react to the results of the tests.
    """

    def __init__(
        self,
        controller_engine: ControllerEngine
    ):
        self.controller_engine = controller_engine
        self.publisher = self.controller_engine.get_results_publisher()
        self.__api_client: Optional[client.ApiClient] = None

    @property
    def api_client(self) -> client.ApiClient:
        """Return the api client."""
        if not self.__api_client:
            self.__api_client = client.ApiClient()
        return self.__api_client

    @staticmethod
    def generate_cron_job(
        kind: str,
        crd: CRD,
        schedule: str,
        task_execution_config: dict,
        the_config: Config,
    ) -> V1CronJob:
        return CronJobHelper.generate_cronjob(
            crd_instance=crd,
            schedule=schedule,
            task_execution_config=task_execution_config,
            config=the_config,
            kind=kind
        )

    def get_results_subscriber(
        self,
        spec,
        crd_manager: CRDInstanceManager
    ) -> IResultsSubscriber:
        """Return the results' subscriber to react to the results test."""
        return ResultsReportSubscriber(
            schedule=spec['schedule'],
            crd_manager=crd_manager,
        )

    def get_crd_for_creation(
        self,
        namespace: str,
        metadata_name: str,
        api_plural: str
    ) -> CRD:
        """Return a CRD instance prepared for the creation lifecycle event."""
        # Generate a worker_task_id based on static information
        worker_task_id = sha1(
            f"{namespace}/{metadata_name}".encode('utf-8')
        ).hexdigest()[:8]

        return CRD(
            namespace=namespace,
            metadata_name=metadata_name,
            cron_job_name=f"{metadata_name}-{worker_task_id[:6]}",
            worker_task_id=worker_task_id,
            plural=api_plural
        )

    def initialize_results_listeners(
        self,
        crd: CRD,
        spec: dict,
        crd_manager: CRDInstanceManager
    ) -> IResultsSubscriber:
        # Listen for the results of the execution task that run in a pod
        # controlled by a CronJob running on a specific namespace.
        logger.debug(
            "Initialize results listeners for %s/%s",
            crd.namespace,
            crd.metadata_name
        )

        # A listener to change the status of the CRD based on the
        # test execution result
        result_subscriber = self.get_results_subscriber(
            spec=spec,
            crd_manager=crd_manager
        )
        self.publisher.add_results_listener(
            execution_id=crd.worker_task_id,
            subscriber=result_subscriber
        )

        # A listener to watch and ensure the result are received in time.
        deadline_validator = ResultsDeadlineValidator(
            schedule=spec['schedule'],
            worker_task_id=crd.worker_task_id,
            controller_engine=self.controller_engine,
            crd_manager=crd_manager
        )
        self.publisher.add_results_listener(
            execution_id=crd.worker_task_id,
            subscriber=deadline_validator
        )

        return result_subscriber

    def remove_all_listeners(self, worker_task_id):
        self.publisher.remove_results_listeners(
            execution_id=worker_task_id
        )

    def suspend_operations(self, crd_manager: CRDInstanceManager):
        """Suspend the operations for the CRD instance."""
        self.publisher.remove_results_listeners(
            execution_id=crd_manager.crd_data.worker_task_id
        )

    def resume_operations(self, crd_manager: CRDInstanceManager, spec: dict):
        """Resume the operations for the CRD instance."""
        self.initialize_results_listeners(
            crd_manager.crd_data,
            spec,
            crd_manager
        )

