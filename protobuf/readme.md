This directory must only contain protobuf files.


- Why this directory is in this path?
Due to the generation of the protobuf files, the path of the generated files is the same as the path of the original files. This is a limitation of the protoc tool.


Usage example:
```shell
 python3 -m grpc_tools.protoc -I protos --python_out=.  --pyi_out=. --grpc_python_out=. ./protos/kubekarma/shared/pb2/*.proto
 ```

This will generate the files under the path `kubekarma/controlleroperator/grpc/pb2/*`

```shell
buf generate  protobuf/
```