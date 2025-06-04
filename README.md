# Basic test
Folder `basic_test` contains a basic test using `grpcurl` and `pytest` for a simple gRPC service.

You can run the test with the following command:

Pytest

```bash
python3 basic_test/test_sayhello.py
```
grpcurl
```bash
./basic_test/test_grpcurl.sh
```


# Base HTTP tester
Folder `base_http_tester` contains our own implementation of a gRPC server and client, along with a simple test for them.

You can run the following command to start the server or the client:

gRPC API server and client:
```bash
python3  base_http_tester/grpc_server.py #  A simple gRPC API server
```
```bash
python3  base_http_tester/grpc_client.py # A simple gRPC API client
```

h2 gRPC server and client:
```bash
python3  base_http_tester/server.py # Our own implementation of gRPC server
```
```bash
python3  base_http_tester/client.py # Our own implementation of gRPC client
```

# Other folders
Folder `fake_http_server` contains our experimental implementation of a gRPC server and client, which cannot interact correctly with `grpcurl`.

Folder `fuzz` contains our own implementation of a fuzzing framework for gRPC server and client, but it is currently non-functional.


