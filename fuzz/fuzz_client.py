import afl
import grpc
import greeter_pb2
import greeter_pb2_grpc
import sys

def main():
    afl.init()
    channel = grpc.insecure_channel('localhost:50052')
    stub = greeter_pb2_grpc.GreeterStub(channel)

    while afl.loop():
        with open("QQ.txt", "a") as f:
            f.write("LOOP ENTERED\n")

        try:
            data = sys.stdin.buffer.read()

            with open("log.txt", "a") as f:
                f.write(data.decode('utf-8', errors='ignore') + "\n")

            msg = greeter_pb2.TestMessage()
            msg.ParseFromString(data)

            response = stub.SendData(msg)

            with open("debug.log", "a") as f:
                f.write("Response: " + response.result + "\n")

        except Exception as e:
            with open("error.log", "a") as f:
                f.write(f"Exception: {str(e)}\n")

if __name__ == '__main__':
    main()
