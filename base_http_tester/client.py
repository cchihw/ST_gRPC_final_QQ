import socket
import struct
import messages_pb2
from h2.connection import H2Connection
from h2.config import H2Configuration

# 建立 request
req = messages_pb2.SimpleRequest()
req.response_size = 10
req.payload.body = b'\x44' * 10
msg = req.SerializeToString()
grpc_payload = b'\x00' + struct.pack(">I", len(msg)) + msg

# 初始化 h2 connection
config = H2Configuration(client_side=True)
conn = H2Connection(config=config)
conn.initiate_connection()
preface = conn.data_to_send()

# 連線
s = socket.create_connection(("localhost", 50051))
s.sendall(preface)

# 建立 stream id = 1
headers = [
    (':method', 'POST'),
    (':scheme', 'http'),
    (':path', '/grpc.testing.TestService/UnaryCall'),
    (':authority', 'localhost'),
    ('content-type', 'application/grpc'),
    ('te', 'trailers'),
]

stream_id = 1
conn.send_headers(stream_id, headers)
conn.send_data(stream_id, grpc_payload, end_stream=True)
s.sendall(conn.data_to_send())

# 收資料
resp = b""
while True:
    chunk = s.recv(65535)
    if not chunk:
        break
    events = conn.receive_data(chunk)
    for ev in events:
        if hasattr(ev, "data"):
            resp += ev.data
    s.sendall(conn.data_to_send())
    if any(ev.__class__.__name__ == 'StreamEnded' for ev in events):
        break

# 解 protobuf
resp_flag = resp[0]
resp_len = struct.unpack(">I", resp[1:5])[0]
resp_payload = resp[5:5 + resp_len]

response = messages_pb2.SimpleResponse()
response.ParseFromString(resp_payload)
print("Decoded response:", response)
