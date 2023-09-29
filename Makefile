# HELP
# This will output the help for each task
# thanks to https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.PHONY: help all
SHELL=/bin/bash

docker_registry = private-registry.xcade.net/kubernetes/cluster-unhealthy-spammer

all: help

generate-python-code: ## Generate python code from .proto
	# first generate shared code
	@python3 -m grpc_tools.protoc -I ./protos --python_out=kubekarma/  --pyi_out=kubekarma/ --grpc_python_out=kubekarma/ protos/kubekarma/shared/pb2/*.proto; \
	# generate controller code
	@python3 -m grpc_tools.protoc -I ./protos/kubekarma --python_out=kubekarma/  --pyi_out=kubekarma/ --grpc_python_out=kubekarma/ protos/kubekarma/shared/pb2/*.proto
