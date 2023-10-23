# KubeKarma

## What is KubeKarma?
KubeKarma is a tool for continuous testing of Kubernetes applications. Currently, KubeKarma supports the following types of tests:

NetworkTestSuite

- `NetworkTestSuite`

## Application Acceptance Continuous Test (AACT)
**I define this test as an Application Acceptance Continuous Test (AACT).**

The test's main point of view is the application itself; it tests if the application 
has the correct configuration in the platform to run correctly. As the infrastructure can change
eventually, the execution of the test periodically ensures that the application can still run correctly.

For instance, the network policies of the Kubernetes infrastructure can change, and the application can be affected. Still, not only because of the NetworkPolicies but also because of the underlying layers of the networks (VPC, Subnets, Firewall rules, Security Groups, etc.).

### Benefits of AACT

- **Increased Confidence**: It provides greater confidence that the application will run smoothly at any time, even after changes to the infrastructure.
- **Early Problem Detection**: It enables early detection of configuration or compatibility issues that could impact the application's performance.
- **Facilitated Troubleshooting**: AACT aids in Troubleshooting by providing a baseline of expected behaviour for the 
application within its environment. When issues or anomalies arise, it becomes easier to pinpoint the root causes 
because the continuous testing process establishes a clear understanding of how the application should operate under 
normal circumstances.


### Tech Stack behind KubeKarma

- [Kubernetes](https://kubernetes.io/)
- [Skaffold](https://skaffold.dev/)
- [Minikube](https://minikube.sigs.k8s.io/docs/)
- [Docker](https://www.docker.com/)
- [Python](https://www.python.org/)

## Usage

[Helm](https://helm.sh) must be installed to use the charts.  Please refer to
Helm's [documentation](https://helm.sh/docs) to get started.

Once Helm has been set up correctly, add the repo as follows:

```shell
  helm repo add kubekarma-repo https://cristiansteib.github.io/kubekarma/
```

If you had already added this repo earlier, run `helm repo update` to retrieve
the latest versions of the packages.  You can then run `helm search repo
kubekarma` to see the charts.

To install the `kubekarma` operator chart:

```shell
    helm install kubekarma kubekarma-repo/kubekarma
```

To uninstall the chart:
```shell
    helm delete kubekarma
```


## Development

```shell
minikube profile custom
minikube start -p custom
skaffold dev --port-forward
```


