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
kubectl apply -f examples/NetworkTestSuite/test_with_all_asserts.yaml
```

## Generate CRD manifests

https://book.kubebuilder.io/getting-started
**NOTE** Please export `GO111MODULE=on` and the binary would be installed at `$GOPATH/bin`.
```shell
 go get  sigs.k8s.io/controller-tools/cmd/controller-gen@v0.14.0
 
```




curl -L -o kubebuilder "https://go.kubebuilder.io/dl/latest/$(go env GOOS)/$(go env GOARCH)"
chmod +x kubebuilder && mv kubebuilder /usr/local/bin/

