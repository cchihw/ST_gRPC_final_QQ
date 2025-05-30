# grpc_client.py
import grpc
import messages_pb2
import messages_pb2_grpc

def run():
    channel = grpc.insecure_channel("localhost:50051")
    stub = messages_pb2_grpc.TestServiceStub(channel)

    request = messages_pb2.SimpleRequest(response_size=10)
    response = stub.UnaryCall(request)
    print("Received:", response)

if __name__ == "__main__":
    run()
