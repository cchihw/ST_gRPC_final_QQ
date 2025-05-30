# python3 -m unittest client.py
# python3 client.py --single_test
# python3 client.py --run_test

import socket
import struct
import argparse
import messages_pb2
from h2.connection import H2Connection
from h2.config import H2Configuration
import h2
import itertools
import unittest
from parameterized import parameterized

def create_grpc_payload(response_size=10, body_byte=b'\x44',if_msg_test=False):
    req = messages_pb2.SimpleRequest()
    req.response_size = response_size
    req.payload.body = body_byte * response_size
    msg = req.SerializeToString()
    if if_msg_test:
        return b'\x00' + struct.pack(">I", len(msg))    
    # gRPC frame header: 1 byte compression flag + 4 bytes length prefix
    return b'\x00' + struct.pack(">I", len(msg))+ msg


def build_headers(method='POST', scheme='https', path='/grpc.testing.TestService/UnaryCall',
                  authority='localhost:50051', content_type='application/grpc', trailers='trailers'):
    return [
        (':method', method),
        (':scheme', scheme),
        (':path', path),
        (':authority', authority),
        ('content-type', content_type),
        ('te', trailers),
    ]


def send_grpc_request(sock, conn, stream_id, headers, payload):
    try:
        conn.send_headers(stream_id, headers)
        conn.send_data(stream_id, payload, end_stream=True)
        sock.sendall(conn.data_to_send())
        return True
    except Exception as e:
        print("Exception in send_grpc_request: ", e)
        conn.close_connection()
        sock.close()
        return False


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

    return resp, status_code


def decode_response(resp):
    if len(resp) < 5:
        raise ValueError("Invalid response, too short.")
    resp_flag = resp[0]
    resp_len = struct.unpack(">I", resp[1:5])[0]
    resp_payload = resp[5:5 + resp_len]
    response = messages_pb2.SimpleResponse()
    response.ParseFromString(resp_payload)
    return response

def grpc_request(method,scheme,path,authority,content_type,trailers,response_size=10,body_byte=b'\x44',if_msg_test=False):
    config = H2Configuration(client_side=True)
    conn = H2Connection(config=config)
    conn.initiate_connection()
    preface = conn.data_to_send()

    stream_id = 1  # gRPC uses stream ID 1 for the first request
    headers = build_headers(method=method, scheme=scheme, path=path, authority=authority, content_type=content_type, trailers=trailers)
    payload = create_grpc_payload(response_size=response_size, body_byte=body_byte,if_msg_test=if_msg_test)

    status_code = None
    with socket.create_connection(("localhost", 50051)) as sock:
        sock.sendall(preface)
        if send_grpc_request(sock, conn, stream_id, headers, payload) == False:
            return None, None
        try:
            resp, status_code = receive_grpc_response(sock, conn)
            response = decode_response(resp)
            return response, status_code
        except Exception as e:
            print("Failed to decode response:", e)
            return None, status_code
        
def single_test():
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
            resp, status_code = receive_grpc_response(sock, conn)
            response = decode_response(resp)
            print("Decoded response:", response)
        except Exception as e:
            print("Failed to decode response:", e)
            # print("Raw response bytes:", resp.hex())

def run_test():
    method_list=['POST','GET','PUT','DELETE']
    scheme_list=['http']
    path_list=['/grpc.testing.TestService/UnaryCall','/grpc.testing.TestService/BadUnaryCall']
    authority_list=['localhost']
    content_type_list=['application/grpc', 'application/grpc+proto']
    trailers_list=['trailers', 'trailers+grpc']
    response_size_list=[10, 100, 500]
    body_byte_list=[b'\x44', b'\x42']
    if_msg_test_list=[True, False]
    
    cnt=0
    for combination in itertools.product(
        method_list, scheme_list, path_list, authority_list,
        content_type_list, trailers_list, response_size_list,
        body_byte_list, if_msg_test_list
    ):
        method, scheme, path, authority, content_type, trailers, response_size, body_byte, if_msg_test = combination
        print("\n\nThe test %d is running..." % cnt)
        cnt += 1
        print(f"Testing {method} {scheme} {path} {authority} {content_type} {trailers} {response_size} {body_byte} {if_msg_test}")
        res, status_code=grpc_request(
            method=method,
            scheme=scheme,
            path=path,
            authority=authority,
            content_type=content_type,
            trailers=trailers,
            response_size=response_size,
            body_byte=body_byte,
            if_msg_test=if_msg_test
        )

        if res:
            print(f"Received response: {res.payload.body}... (length={len(res.payload.body)})")
        else:
            print("No response received or failed to decode.")

def generate_test_cases():
    method_list = ['POST', 'GET', 'PUT']
    scheme_list = ['http']
    path_list = ['/grpc.testing.TestService/UnaryCall', '/grpc.testing.TestService/BadUnaryCall']
    authority_list = ['localhost']
    content_type_list = ['application/grpc', 'application/grpc+proto']
    trailers_list = ['trailers', 'trailers+grpc']
    response_size_list = [10]
    body_byte_list = [b'\x44', b'\x45']
    if_msg_test_list = [True, False]

    return list(itertools.product(
        method_list, scheme_list, path_list, authority_list,
        content_type_list, trailers_list, response_size_list,
        body_byte_list, if_msg_test_list
    ))

class TestCombinations(unittest.TestCase):
    @parameterized.expand(generate_test_cases())
    def test_combination(self, method, scheme, path, authority,
        content_type, trailers, response_size,
        body_byte, if_msg_test
    ):
        print(f"Testing {method} {scheme} {path} {authority} {content_type} {trailers} {response_size} {body_byte} {if_msg_test}")

        res, status_code=grpc_request(
            method=method,
            scheme=scheme,
            path=path,
            authority=authority,
            content_type=content_type,
            trailers=trailers,
            response_size=response_size,
            body_byte=body_byte,
            if_msg_test=if_msg_test
        )

        print("status_code", status_code)
        if trailers == 'trailers+grpc':
            self.assertEqual(status_code, None)
            self.assertEqual(res, None)
        elif method != "POST":
            self.assertEqual(status_code, 2) 
        elif if_msg_test == True:
            self.assertEqual(status_code, 12) 
        elif path == '/grpc.testing.TestService/BadUnaryCall':
            self.assertEqual(status_code, 12)
        else:
            self.assertEqual(status_code, 0)


def main():
    #arg parser
    parser = argparse.ArgumentParser(description="gRPC client tester")
    parser.add_argument('--run_test', action='store_true', help="Run the full test suite")
    parser.add_argument('--single_test', action='store_true', help="Run a single gRPC request test")
    args = parser.parse_args()

    if args.run_test:
        # Run the full test suite
        print("Running full gRPC test suite...")
        run_test()
    elif args.single_test:
        # Run a single gRPC request test
        print("Running single gRPC request test...")
        single_test()
    #Testing single gRPC request
    # print("Recieve payload from gRPC server:", single_test())
    ## End Testing single gRPC request



if __name__ == "__main__":
    main()
