import afl  # python-afl
import grpc
import greeter_pb2
import greeter_pb2_grpc
import sys

def main():
    channel = grpc.insecure_channel('localhost:50052')
    stub = greeter_pb2_grpc.TestServiceStub(channel)

    afl.init()

    while afl.loop():
        try:
            # 從 stdin 讀入 serialized message
            data = sys.stdin.buffer.read()
            # 嘗試反序列化為 TestMessage
            msg = greeter_pb2.TestMessage()
            msg.ParseFromString(data)
            # 傳送給 gRPC server
            response = stub.SendData(msg)
        except Exception as e:
            pass  # 忽略例外，讓 fuzzer 繼續嘗試

if __name__ == '__main__':
    main()
