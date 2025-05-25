from concurrent import futures
from grpc_reflection.v1alpha import reflection
import grpc
import greeter_pb2
import greeter_pb2_grpc
import time

class GreeterServicer(greeter_pb2_grpc.GreeterServicer):
    def SayHello(self, request, context):
        if request.name == "slow":
            time.sleep(1)
        return greeter_pb2.HelloReply(message=f"Hello, {request.name}!")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    greeter_pb2_grpc.add_GreeterServicer_to_server(GreeterServicer(), server)

    SERVICE_NAMES = (
        greeter_pb2.DESCRIPTOR.services_by_name['Greeter'].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)

    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC server with reflection started")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
