# grpc_server.py
import grpc
from concurrent import futures
import time
import messages_pb2
import messages_pb2_grpc

class TestService(messages_pb2_grpc.TestServiceServicer):
    def UnaryCall(self, request, context):
        print(f"Received request: response_size={request.response_size}")

        if request.response_size < 0:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("response_size must be non-negative")
            return messages_pb2.SimpleResponse()

        payload_body = b"B" * request.response_size
        payload = messages_pb2.Payload(body=payload_body)
        return messages_pb2.SimpleResponse(payload=payload)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    messages_pb2_grpc.add_TestServiceServicer_to_server(TestService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("gRPC server listening on port 50051...")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    serve()
