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
import dataclasses
import uuid
from hashlib import sha1
from typing import List, Optional, Type

import kopf
import yaml
from kopf import Spec
from kubernetes import client
from kubernetes.client import V1CronJob

from kubekarma.controlleroperator import ITestResultsPublisher
from kubekarma.controlleroperator.abc.resultspublisher import \
    IResultsSubscriber
from kubekarma.controlleroperator.config import Config, config
from kubekarma.controlleroperator.engine.controllerengine import \
    ControllerEngine
from kubekarma.controlleroperator.kinds.crdinstancemanager import CRD, \
    CRDInstanceManager
from kubekarma.controlleroperator.kinds.cronjob import CronJobHelper

import logging

logger = logging.getLogger(__name__)


class ICrdValidator(abc.ABC):

    @abc.abstractmethod
    def validate_spec(self, spec) -> List[str]:
        """Perform validations on the spec of the CRD."""


@dataclasses.dataclass
class TestSuiteKindContext:
    ...


class TestSuiteKindBase(abc.ABC):
    """This class provides the base functionality for a TestSuiteKind.

    A TestSuiteKind is a kind of CRD that is used to define a test suite
    and this class provides the base functionality to handle the lifecycle
    events of the CRD and to react to the results of the tests.
    """

    def __init__(
        self,
        publisher: ITestResultsPublisher,
        controller_engine: ControllerEngine
    ):
        self.controller_engine = controller_engine
        self.publisher = publisher
        self.__api_client: Optional[client.ApiClient] = None

    @property
    def _api_client(self) -> client.ApiClient:
        """Return the api client."""
        if not self.__api_client:
            self.__api_client = client.ApiClient()
        return self.__api_client

    @property
    @abc.abstractmethod
    def kind(self) -> str:
        """Return the kind of the CRD."""

    @property
    @abc.abstractmethod
    def crd_validator(self) -> Type[ICrdValidator]:
        """Return the validator of the CRD.

        The validator is responsible to validate the spec of the CRD and
        return a list of errors if any.
        """

    @property
    @abc.abstractmethod
    def api_plural(self) -> str:
        """Return the api plural of the CRD."""

    def generate_cron_job(
        self,
        crd: CRD,
        schedule: str,
        spec: dict,
        the_config: Config
    ) -> V1CronJob:
        """Generate the cronjob spec to be used by the cronjob."""
        return CronJobHelper.generate_cronjob(
            crd_instance=crd,
            schedule=schedule,
            task_execution_config=spec,
            config=the_config,
            kind=self.kind
        )

    @abc.abstractmethod
    def get_results_subscriber(
        self,
        spec,
        crd_manager: CRDInstanceManager
    ) -> IResultsSubscriber:
        """Return the results' subscriber to react to the results test."""

    def handle_create(self, spec: Spec, body, **kwargs):
        # I need to copy the context to avoid an error on the kopf framework
        # related to the context management of the handlers, because
        # it uses the contextvars to store the settings of each handler.
        context_copy: contextvars.Context = contextvars.copy_context()

        # Ensure that the kind is the expected one.
        kind = body['kind']
        self.validate_is_expected_kind(kind)

        test_name = spec['name']
        namespace = body['metadata']['namespace']
        kopf.info(
            body,
            reason='CreationReceived',
            message=f'Handling {kind}  <{test_name}>'
        )

        job_id = sha1(f"{namespace}/{test_name}".encode('utf-8')).hexdigest()

        crd = CRD(
            namespace=namespace,
            metadata_name=body['metadata']['name'],
            cron_job_name=f"{body['metadata']['name']}-{job_id[:6]}",
            worker_task_id=uuid.uuid4().hex,
            plural=self.api_plural
        )

        crd_manager = CRDInstanceManager(
            api_client=self._api_client,
            crd_data=crd,
            body=body,
            contextvars_copy=context_copy
        )
        self.validate_kind_spec(spec, crd_manager)
        cron_job = self.generate_cron_job(
            crd=crd,
            schedule=spec['schedule'],
            spec=dict(spec),
            the_config=config
        ).to_dict()

        # Adopt the cronjob to the parent object to be able to delete it
        # in cascade.
        kopf.adopt(cron_job, owner=body)
        # Call the api to create the cronjob
        self.create_cron_job(cron_job, crd)
        subscriber = self.setup_results_subscriber(
            crd.worker_task_id,
            dict(spec),
            crd_manager
        )
        self.setup_watchdog(crd, subscriber)

        # Patch the created CRD with annotation pointing to the created cronjob
        # and the code version used by this handler.
        # This will allow for future version perform the required changes.
        crd_manager.patch_with_cronjob_notation(crd)

        # Trigger an event for the CRD related to the creation of the cronjob
        crd_manager.info_event(
            reason='Running',
            message=f'CronJob created successfully <{crd.cron_job_name}>'
        )

        # Set the phase of the CRD to Active
        crd_manager.set_phase_to_active()

    def setup_results_subscriber(
        self,
        worker_task_id: str,
        spec: dict,
        crd_manager: CRDInstanceManager
    ) -> IResultsSubscriber:
        # Listen for the results of the execution task that run in a pod
        # controlled by a CronJob running on a specific namespace.
        result_subscriber = self.get_results_subscriber(
            spec=spec,
            crd_manager=crd_manager
        )
        self.publisher.add_results_listener(
            execution_id=worker_task_id,
            subscriber=result_subscriber
        )
        return result_subscriber

    def handle_deletion(self):
        pass

    def handle_update(self, spec, body, **kwargs):
        pass

    def handle_resume(self):
        pass

    def handle_pause(self):
        pass

    def receive_results(self):
        pass

    def validate_is_expected_kind(self, kind: str):
        if kind != self.kind:
            self._raise_error(
                "Invlid kind: %s expected %s", kind, self.kind
            )

    def _raise_error(self, param, *args, **kwargs):
        raise RuntimeError(param.format(*args, **kwargs))

    def validate_kind_spec(self, spec, crd_manager: CRDInstanceManager):
        """Perform validations on the spec of the CRD.

        If detects any error it will raise an exception and change the status
        of the CRD to Failed.
        """

        crd_validator = self.crd_validator()
        assert isinstance(crd_validator, ICrdValidator), (
            f"{crd_validator} is not an instance of {ICrdValidator}"
        )
        errors = crd_validator.validate_spec(spec)
        if errors:
            crd_manager.set_phase_to_failed()
            self._raise_error(
                "Invalid spec: %s", errors
            )

    def create_cron_job(self, cron_job,  crd: CRD):
        try:
            client.BatchV1Api(
                api_client=self._api_client
            ).create_namespaced_cron_job(
                namespace=crd.namespace,
                body=cron_job
            )
        except client.exceptions.ApiException as e:
            logger.exception(yaml.dump(e.body))
            raise e

    def setup_watchdog(self, crd, subscriber):
        """Create a watchdog to check if the results are received in time."""
        logger.debug(
            "[TODO] Setting up watchdog for %s",
            crd.cron_job_name
        )


class TestSuiteKindManager:

    def __init__(
        self,
        publisher: ITestResultsPublisher
    ):
        self.publisher = publisher
