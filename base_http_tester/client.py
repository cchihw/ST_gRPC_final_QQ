import socket
import struct
import messages_pb2
from h2.connection import H2Connection
from h2.config import H2Configuration
import h2

def create_grpc_payload(response_size=10, body_byte=b'\x44'):
    req = messages_pb2.SimpleRequest()
    req.response_size = response_size
    req.payload.body = body_byte * response_size*100
    msg = req.SerializeToString()
    # gRPC frame header: 1 byte compression flag + 4 bytes length prefix
    return b'\x00' + struct.pack(">I", len(msg))+ msg


def build_headers(path="/grpc.testing.TestService/UnaryCall"):
    return [
        (':method', 'POST'),
        (':scheme', 'http'),
        (':path', path),
        (':authority', 'localhost'),
        ('content-type', 'application/grpc'),
        ('te', 'trailers'),
    ]


def send_grpc_request(sock, conn, stream_id, headers, payload):
    conn.send_headers(stream_id, headers)
    conn.send_data(stream_id, payload, end_stream=True)
    sock.sendall(conn.data_to_send())


def receive_grpc_response(sock, conn):
    resp = b""
    status_code = None
    status_message = None

    while True:
        chunk = sock.recv(65535)
        if not chunk:
            print("No more data from socket. Connection likely closed.")
            break

        events = conn.receive_data(chunk)
        for ev in events:
            if isinstance(ev, h2.events.ResponseReceived):
                print("Response headers received:")
                for name, value in ev.headers:
                    print(f"  {name.decode()}: {value.decode()}")
                    if name == b'grpc-status':
                        status_code = int(value)
                    if name == b'grpc-message':
                        status_message = value.decode()

            elif isinstance(ev, h2.events.TrailersReceived):
                print("Trailers received:")
                for name, value in ev.headers:
                    print(f"  {name.decode()}: {value.decode()}")
                    if name == b'grpc-status':
                        status_code = int(value)
                    if name == b'grpc-message':
                        status_message = value.decode()

            elif isinstance(ev, h2.events.StreamReset):
                print(f"Stream was reset by server. Error code: {ev.error_code}")

            elif isinstance(ev, h2.events.DataReceived):
                print(f"eceived {len(ev.data)} bytes of data.")
                resp += ev.data

        sock.sendall(conn.data_to_send())

        if any(isinstance(ev, h2.events.StreamEnded) for ev in events):
            break

    if status_code is not None and status_code != 0:
        print(f"gRPC error received: grpc-status={status_code}, message='{status_message}'")

    return resp


def decode_response(resp):
    if len(resp) < 5:
        raise ValueError("Invalid response, too short.")
    resp_flag = resp[0]
    resp_len = struct.unpack(">I", resp[1:5])[0]
    resp_payload = resp[5:5 + resp_len]
    response = messages_pb2.SimpleResponse()
    response.ParseFromString(resp_payload)
    return response


def main():
    config = H2Configuration(client_side=True)
    conn = H2Connection(config=config)
    conn.initiate_connection()
    preface = conn.data_to_send()

    stream_id = 1
    headers = build_headers(path="/grpc.testing.TestService/UnaryCall")  # or use BadUnaryCall to test error
    payload = create_grpc_payload()

    with socket.create_connection(("localhost", 50051)) as sock:
        sock.sendall(preface)
        send_grpc_request(sock, conn, stream_id, headers, payload)
        try:
            resp = receive_grpc_response(sock, conn)
            response = decode_response(resp)
            print("Decoded response:", response)
        except Exception as e:
            print("Failed to decode response:", e)
            # print("Raw response bytes:", resp.hex())


if __name__ == "__main__":
    main()
