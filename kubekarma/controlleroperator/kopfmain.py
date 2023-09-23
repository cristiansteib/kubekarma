import dataclasses
from datetime import datetime
from multiprocessing import Process

import kopf
import logging

import kubernetes


from kubekarma.controlleroperator.handlers import networkpolicytestsuite as npts_handler
from kubekarma.controlleroperator.httpserver import start_server
from kubernetes import client

http_server_process = Process(target=start_server, args=("0.0.0.0",))

_logger = logging.getLogger(__name__)


class KubernetesApi:
    """An abstract layer to talk with the Kubernetes API."""

    def __init__(self, apps_api: kubernetes.client.AppsV1Api):
        self.apps_api = apps_api

    def create_cronjob(
        self,
        namespace: str,
        job_template: dict
    ) -> kubernetes.client.V1CronJob:
        """Create a cronjob in the cluster."""
        return kubernetes.client.BatchV1Api(
            api_client=self.apps_api.api_client
        ).create_namespaced_cron_job(
            namespace=namespace,
            body=job_template
        )

    def mutate_crd_satus(self, body, new_status):
        # TODO: improve this method to be more generic
        c_api = kubernetes.client.CustomObjectsApi(
            api_client=self.apps_api.api_client
        )
        namespace = body['metadata']['namespace']
        api_version = parse_api_version(body['apiVersion'])
        a_object = c_api.get_namespaced_custom_object(
            group=api_version.group,
            version=api_version.version,
            namespace=namespace,
            plural=API_PLURAL,
            name=body['metadata']['name']
        )
        status = a_object.get('status', {})
        status['phase'] = new_status
        a_object['status'] = status
        c_api.patch_namespaced_custom_object(
            group=api_version.group,
            version=api_version.version,
            namespace=namespace,
            plural=API_PLURAL,
            name=body['metadata']['name'],
            body=status
        )


kubernetes_api: KubernetesApi

API_GROUP = 'kubekarma.io'
API_VERSION = 'v1'
API_PLURAL = 'networkpolicytestsuites'


@kopf.on.login()
def login(**kwargs):
    global kubernetes_api
    conn = kopf.login_via_client(**kwargs)
    kubernetes_api = KubernetesApi(client.AppsV1Api())
    return conn


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    # settings.posting.level = logging.DEBUG
    # Events configuration
    settings.posting.level = logging.INFO
    settings.posting.enabled = True
    settings.execution.max_workers = 8
    settings.watching.connect_timeout = 1 * 60
    settings.watching.server_timeout = 5 * 60


@kopf.on.startup()
def start_results_receiver(**kwargs):
    http_server_process.start()


@kopf.on.cleanup()
def stop_results_receiver(**kwargs):
    http_server_process.terminate()


@kopf.on.probe(id='now')
def get_current_timestamp(**kwargs):
    return datetime.utcnow().isoformat()


@dataclasses.dataclass
class ApiVersion:
    group: str
    version: str


def parse_api_version(api_version: str) -> ApiVersion:
    group, version = api_version.split('/')
    return ApiVersion(group=group, version=version)


@kopf.on.create(
    API_GROUP,
    API_VERSION,
    API_PLURAL,
)
def network_policy_created(spec, body, **kwargs):
    kopf.info(
        body,
        reason='Creation received by controller',
        message=f'Handling {body["kind"]}  <{body["spec"]["name"]}>'
    )
    kubernetes_api.mutate_crd_satus(body, 'Pending')
    cron_job_body = npts_handler.handle_npts_creation(body)
    # Adopt the object to propagate the deletion.
    kopf.adopt(cron_job_body)
    cron_job = kubernetes_api.create_cronjob(
        namespace=body['metadata']['namespace'],
        job_template=cron_job_body
    )
    kubernetes_api.mutate_crd_satus(body, 'Running')
    kopf.info(
        body,
        reason='ready',
        message=f'detected creation'
    )