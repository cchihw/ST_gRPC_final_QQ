import grpc
from concurrent import futures
import greeter_pb2
import greeter_pb2_grpc

class TestService(greeter_pb2_grpc.GreeterServicer):
    def SendData(self, request, context):
        print(f"Received: {request.content}")
        return greeter_pb2.TestResponse(result="OK")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    greeter_pb2_grpc.add_GreeterServicer_to_server(TestService(), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    print("Server started on port 50052")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
