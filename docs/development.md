# Start dev environment

## Requirements
Python 3.11


```shell
sudo apt install python3.11-full
```

```shell
minikube profile create custom
minikube start -p custom
skaffold dev --port-forward
kubectl apply -f examples/NetworkKubarmaTestSuite/test_with_all_asserts.yaml
```
