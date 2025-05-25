import grpc
import greeter_pb2
import greeter_pb2_grpc
import sys
import argparse
import datetime

def log_result(test_name, code, detail):
    with open("result.log", "a") as f:
        timestamp = datetime.datetime.now().isoformat()
        f.write(f"[{timestamp}] {test_name} | Code: {code.name} | Detail: {detail}\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", type=str, required=True, help="測試名稱，例如: length_mismatch")
    args = parser.parse_args()

    test_name = args.test
    channel = grpc.insecure_channel('localhost:50051')
    stub = greeter_pb2_grpc.GreeterStub(channel)

    try:
        response = stub.SayHello(greeter_pb2.HelloRequest(name="Test"))
        print("[+] Response:", response.message)
        log_result(test_name, grpc.StatusCode.OK, response.message)
    except grpc.RpcError as e:
        print("[-] Caught RpcError:")
        print("    Code:   ", e.code())
        print("    Detail: ", e.details())
        log_result(test_name, e.code(), e.details())

if __name__ == "__main__":
    main()
