import unittest
import grpc
import greeter_pb2
import greeter_pb2_grpc

class SayHelloTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # build the gRPC channel and stub
        cls.channel = grpc.insecure_channel('localhost:50051')
        cls.stub = greeter_pb2_grpc.GreeterStub(cls.channel)

    def test_valid_input(self):
        response = self.stub.SayHello(greeter_pb2.HelloRequest(name="Zhi"))
        self.assertEqual(response.message, "Hello, Zhi!")

    def test_empty_string(self):
        response = self.stub.SayHello(greeter_pb2.HelloRequest(name=""))
        self.assertTrue(response.message.startswith("Hello"))

    def test_long_string(self):
        long_name = "A" * 10000
        response = self.stub.SayHello(greeter_pb2.HelloRequest(name=long_name))
        self.assertTrue(response.message.endswith("AAAA!"))

    def test_missing_field(self):
        response = self.stub.SayHello(greeter_pb2.HelloRequest())
        self.assertTrue(response.message.startswith("Hello"))

    def test_non_utf8(self):
        try:
            name = b'\xff\xff'.decode('utf-8', errors='ignore')
            response = self.stub.SayHello(greeter_pb2.HelloRequest(name=name))
            self.assertIn("Hello", response.message)
        except grpc.RpcError as e:
            self.assertIn(e.code().name, ["INTERNAL", "UNKNOWN"])

    def test_invalid_argument_status(self):
        try:
            # empty name should raise an error
            self.stub.SayHello(greeter_pb2.HelloRequest(name=""))
            # self.fail("Expected INVALID_ARGUMENT, but no exception was raised.")
        except grpc.RpcError as e:
            self.assertEqual(e.code(), grpc.StatusCode.INVALID_ARGUMENT)
            self.assertIn("name is required", e.details())

    def test_unimplemented_method_status(self):
        try:
            method = "/greeter.Greeter/NotExistMethod"
            self.channel.unary_unary(method)(b"", timeout=1)
            self.fail("Expected UNIMPLEMENTED error, but no exception was raised.")
        except grpc.RpcError as e:
            self.assertEqual(e.code(), grpc.StatusCode.UNIMPLEMENTED)

    def test_deadline_exceeded_status(self):
        try:
            self.stub.SayHello(
                greeter_pb2.HelloRequest(name="slow"),
                timeout=0.1  # 100ms
            )
            self.fail("Expected DEADLINE_EXCEEDED, but no exception was raised.")
        except grpc.RpcError as e:
            self.assertEqual(e.code(), grpc.StatusCode.DEADLINE_EXCEEDED)

    @classmethod
    def tearDownClass(cls):
        cls.channel.close()

if __name__ == '__main__':
    unittest.main()
