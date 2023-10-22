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
from hashlib import sha1
from typing import Optional, Type

import kopf
import yaml
from kopf import Body, Spec
from kubernetes import client
from kubernetes.client import V1CronJob

from kubekarma.controlleroperator import ITestResultsPublisher
from kubekarma.controlleroperator.core.abc.resultspublisher import \
    IResultsSubscriber
from kubekarma.controlleroperator.config import Config, config
from kubekarma.controlleroperator.core.abc.crdvalidator import ICrdValidator
from kubekarma.controlleroperator.core.controllerengine import \
    ControllerEngine
from kubekarma.controlleroperator.core.crdinstancemanager import CRD, \
    CRDInstanceManager
from kubekarma.controlleroperator.core.cronjob import CronJobHelper

import logging

from kubekarma.controlleroperator.core.testsuite.resultsdeadline import \
    ResultsDeadlineValidator
from kubekarma.controlleroperator.core.testsuite.resultssubscriber import \
    ResultsSubscriber

logger = logging.getLogger(__name__)


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

    def get_results_subscriber(
        self,
        spec,
        crd_manager: CRDInstanceManager
    ) -> IResultsSubscriber:
        """Return the results' subscriber to react to the results test."""
        return ResultsSubscriber(
            schedule=spec['schedule'],
            crd_manager=crd_manager,
        )

    def __get_crd(
        self,
        namespace: str,
        body: Body,
        cronjob_name: Optional[str] = None,
        worker_task_id: Optional[str] = None
    ) -> CRD:
        """Build the CRD instance.

        The object contains the information of the CRD instance, that can
        be used to identify the related resources.

        Args:
            namespace: The namespace of the CRD instance.
            body: The body of the CRD instance.
            cronjob_name: The name of the cronjob related to the CRD instance.
                This argument is optional because the cronjob name is unknown
                at the creation time, but for later operations it is
                available in the .metadata.annotations
            worker_task_id: The id of the worker task that is running the
                tests. This argument is optional because the worker task id
                is unknown at the creation time, but for later operations it
                is available in the .metadata.annotations
        Returns:
            The CRD data object.

        * This is a helper method.

        """
        return CRD(
            namespace=namespace,
            metadata_name=body['metadata']['name'],
            # TODO: consume the cronjob name from the annotations
            cron_job_name=cronjob_name,
            # TODO: consume the worker task id from the annotations
            worker_task_id=worker_task_id,
            plural=self.api_plural
        )

    def __get_crd_manager(
        self,
        body: Body,
        crd: CRD,
    ) -> CRDInstanceManager:
        # I need to copy the context to avoid an error on the kopf framework
        # related to the context management of the handlers, because
        # it uses the contextvars to store the settings of each handler.
        context_copy: contextvars.Context = contextvars.copy_context()
        return CRDInstanceManager(
            api_client=self._api_client,
            crd_ctx=crd,
            body=body,
            contextvars_copy=context_copy
        )

    def handle_create(self, spec: Spec, body, **kwargs):
        """Handle the creation of the CRD instance."""

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

        job_id = sha1(
            f"{namespace}/{test_name}".encode('utf-8')
        ).hexdigest()[:8]

        crd = self.__get_crd(
            namespace=namespace,
            body=body,
            cronjob_name=f"{body['metadata']['name']}-{job_id[:6]}",
            worker_task_id=job_id
        )

        crd_manager = self.__get_crd_manager(
            body=body,
            crd=crd
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

        # Store the information of the CRD instance
        crd_manager.save()

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

        # A listener to change the status of the CRD based on the
        # test execution result
        result_subscriber = self.get_results_subscriber(
            spec=spec,
            crd_manager=crd_manager
        )
        self.publisher.add_results_listener(
            execution_id=worker_task_id,
            subscriber=result_subscriber
        )

        # A listener to watch and ensure the result are received in time.
        deadline_validator = ResultsDeadlineValidator(
            schedule=spec['schedule'],
            cron_job_name=crd_manager.crd_data.cron_job_name,
            controller_engine=self.controller_engine
        )
        self.publisher.add_results_listener(
            execution_id=worker_task_id,
            subscriber=deadline_validator
        )

        return result_subscriber

    def handle_delete(self, spec, body, **kwargs):
        """Handle the deletion of the CRD instance.

        All Kubernetes objects related should be deleted, also the
        instance classes should be deleted.

        Class Services related:
        - Publisher
        - ResultsSubscriber
        - CRDInstanceManager
        """
        logger.info("[%s] Cleaning the room for the %s", self.kind, body['metadata']['name'])
        return
        # ctx = object()
        # self.publisher.remove_results_listeners(
        #     execution_id=ctx.worker_task_id
        # )

    def handle_update(self, spec, body, **kwargs):
        pass

    def handle_resume_controller_restart(self, spec, body, **kwargs):
        """Resume the controller operations for the CRD on restart."""
        logger.debug("Resuming %s", body['metadata']['name'])

    def handle_suspend(self, spec, body, **kwargs):
        """Pause the controller operations for the CRD."""
        logger.debug("Pausing %s", body['metadata']['name'])
        crd_manager = self.__get_crd_manager(
            body=body,
            crd=self.__get_crd(
                namespace=body['metadata']['namespace'],
                body=body
            )
        )
        if spec['suspend']:
            crd_manager.set_phase_to_suspended()
            # TODO: suspend related cronjob
        else:
            # TODO: resume related cronjob
            crd_manager.set_phase_to_active()

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

    def create_cron_job(self, cron_job, crd: CRD):
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
