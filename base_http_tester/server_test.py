# python3 -m unittest server_test.py

import socket
import threading
import logging

from h2.config import H2Configuration
from h2.connection import H2Connection
from h2_server import H2ServerConnection

import h2.connection
import handlers
import struct
import unittest
import grpc
import messages_pb2
import messages_pb2_grpc
import threading
import time
from parameterized import parameterized

HOST = '0.0.0.0'
PORT = 50051 

logging.basicConfig(level=logging.INFO)


class H2ServerConnection2(H2ServerConnection):
    def send_response(self, stream_id, response_bytes):
        # Send gRPC response (header + data + trailer)
        self.conn.send_headers(
            stream_id=stream_id,
            headers=[
                (":status", "404"),
                ("content-type", "application/grpc"),
                ("grpc-encoding", "identity"),
                ("grpc-accept-encoding", "identity"),
            ],
        )

        grpc_payload = (
            b"\x00" + struct.pack(">I", len(response_bytes)) + response_bytes
        )   
        self.conn.send_data(stream_id, grpc_payload)
        self.conn.send_headers(
            stream_id=stream_id,
            headers=[("grpc-status", "0"), ("grpc-message", "Haha")],
            end_stream=True,
        )

class H2ServerConnection3(H2ServerConnection):
    def send_response(self, stream_id, response_bytes):
        # Send gRPC response (header + data + trailer)
        self.conn.send_headers(
            stream_id=stream_id,
            headers=[
                (":status", "200"),
                ("content-type", "application/grpc"),
                ("grpc-encoding", "identity"),
                ("grpc-accept-encoding", "identity"),
            ],
        )

        grpc_payload = (
            b"\x00" + struct.pack(">I", len(response_bytes)) + response_bytes
        )   
        self.conn.send_data(stream_id, grpc_payload)
        self.conn.send_headers(
            stream_id=stream_id,
            headers=[("grpc-status", "10"), ("grpc-message", "Haha")],
            end_stream=True,
        )

class H2ServerConnection4(H2ServerConnection):
    def send_response(self, stream_id, response_bytes):
        # Send gRPC response (header + data + trailer)
        self.conn.send_headers(
            stream_id=stream_id,
            headers=[
                (":status", "200"),
                ("content-type", "application/grpc"),
                ("grpc-encoding", "identity"),
                ("grpc-accept-encoding", "identity"),
            ],
        )

        grpc_payload = (
            b"\x00" + struct.pack(">I", len(response_bytes)+10) + response_bytes
        )   
        self.conn.send_data(stream_id, grpc_payload)
        self.conn.send_headers(
            stream_id=stream_id,
            headers=[("grpc-status", "0"), ("grpc-message", "Haha")],
            end_stream=True,
        )

def handle_client_connection(conn, addr, h2_server_class=H2ServerConnection, stop_event=None):
    logging.info(f"Accepted connection from {addr}")
    h2_conn = h2_server_class()
    conn.sendall(h2_conn.initiate_connection())

    h2_conn.set_handler("request", handlers.on_request)
    h2_conn.set_handler("data", handlers.on_data_factory(h2_conn))

    try:
        while not stop_event.is_set():
            data = conn.recv(65535)
            if not data:
                break

            to_send = h2_conn.receive_data(data)
            if to_send:
                conn.sendall(to_send)

    except Exception as e:
        logging.error(f"Exception: {e}")
    finally:
        conn.close()
        logging.info(f"Closed connection from {addr}")


def build_server(h2_server_class=H2ServerConnection, stop_event=None):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    server_socket.settimeout(2)
    logging.info(f"gRPC test server listening on {HOST}:{PORT}")

    try:
        while not stop_event.is_set():
            try:
                conn, addr = server_socket.accept()
            except socket.timeout:
                continue 
            client_thread = threading.Thread(
                target=handle_client_connection, args=(conn, addr, h2_server_class, stop_event), daemon=True
            )
            client_thread.start()
    except KeyboardInterrupt:
        logging.info("Shutting down server")
    finally:
        server_socket.close()

        
class TestCombinations(unittest.TestCase):
    def start_server(self, h2_server_class=H2ServerConnection):
        self.stop_event = threading.Event()
        self.server_thread = threading.Thread(
            target=build_server,
            args=(h2_server_class, self.stop_event, ),
            daemon=True
        )
        self.server_thread.start()
        time.sleep(1) 

    def tearDown(self):
        if hasattr(self, "stop_event"):
            self.stop_event.set()
        if hasattr(self, "server_thread"):
            self.server_thread.join()
            time.sleep(0.5)

    def client_test(self, status_code):
        self.assertTrue(True)
        # Setup gRPC client
        channel = grpc.insecure_channel(f"{HOST}:{PORT}")
        stub = messages_pb2_grpc.TestServiceStub(channel)
        request = messages_pb2.SimpleRequest(response_size=10)

        # Make a call and check response
        try:
            response = stub.UnaryCall(request)
            if status_code != None:
                self.assertIsNotNone(response)
            else:
                self.assertIsNone(response)
        except grpc.RpcError as e:
            print("[!] gRPC Error Caught")
            print(" - code   :", e.code()) 
            print(" - details:", e.details())   
            print(" - trailing metadata:", e.trailing_metadata())
            self.assertEqual(e.code(), status_code) 

    @parameterized.expand([
        (H2ServerConnection, grpc.StatusCode.OK),
        (H2ServerConnection2, grpc.StatusCode.UNIMPLEMENTED),
        (H2ServerConnection3, grpc.StatusCode.ABORTED),
        (H2ServerConnection4, None),
    ])
    def test_server_response(self, h2_class, expected_status):
        self.start_server(h2_class)
        self.client_test(expected_status)
        

if __name__ == "__main__":
    build_server()
