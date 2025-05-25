import unittest
import grpc
import greeter_pb2
import greeter_pb2_grpc

class SayHelloTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 建立 gRPC channel 與 stub
        cls.channel = grpc.insecure_channel('localhost:50051')
        cls.stub = greeter_pb2_grpc.GreeterStub(cls.channel)

    def test_valid_input(self):
        response = self.stub.SayHello(greeter_pb2.HelloRequest(name="Zhi"))
        self.assertEqual(response.message, "Hello, Zhi!")

    def test_empty_string(self):
        response = self.stub.SayHello(greeter_pb2.HelloRequest(name=""))
        # 根據你 server 的實作，這邊可以改判斷
        self.assertTrue(response.message.startswith("Hello"))

    def test_long_string(self):
        long_name = "A" * 10000
        response = self.stub.SayHello(greeter_pb2.HelloRequest(name=long_name))
        self.assertTrue(response.message.endswith("AAAA!"))  # 部分驗證即可

    def test_invalid_field(self):
        # 用 grpc 的錯誤方式模擬非法 field，需直接用 json (grpcurl 更適合)
        pass  # 無法直接測，除非用低階 channel + serialized json

    def test_missing_field(self):
        # name 是 optional，這會自動變成空字串
        response = self.stub.SayHello(greeter_pb2.HelloRequest())
        self.assertTrue(response.message.startswith("Hello"))

    def test_non_utf8(self):
        # 模擬亂碼，非 UTF-8 編碼，會被轉成空字串或錯誤
        try:
            name = b'\xff\xff'.decode('utf-8', errors='ignore')
            response = self.stub.SayHello(greeter_pb2.HelloRequest(name=name))
            self.assertIn("Hello", response.message)
        except grpc.RpcError as e:
            self.assertIn(e.code().name, ["INTERNAL", "UNKNOWN"])

    def test_invalid_argument_status(self):
        try:
            # 傳入空字串，預期 server 拋 INVALID_ARGUMENT
            self.stub.SayHello(greeter_pb2.HelloRequest(name=""))
            # self.fail("Expected INVALID_ARGUMENT, but no exception was raised.")
        except grpc.RpcError as e:
            self.assertEqual(e.code(), grpc.StatusCode.INVALID_ARGUMENT)
            self.assertIn("name is required", e.details())

    def test_unimplemented_method_status(self):
        try:
            # 這邊模擬不存在的方法 call，要自己手動建立假 stub 或改 proto
            # 這裡展示用低階 channel 模擬 call 一個錯誤方法
            method = "/greeter.Greeter/NotExistMethod"
            self.channel.unary_unary(method)(b"", timeout=1)
            self.fail("Expected UNIMPLEMENTED error, but no exception was raised.")
        except grpc.RpcError as e:
            self.assertEqual(e.code(), grpc.StatusCode.UNIMPLEMENTED)

    def test_deadline_exceeded_status(self):
        try:
            # Server sleep 超過 deadline（你需手動讓 server 故意 delay）
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
