# Start dev environment

```shell
minikube profile create custom
minikube start -p custom
skaffold dev --port-forward
kubectl apply -f examples/NetworkTestSuite/test_with_all_asserts.yaml
```
