import socket
import threading
import logging

from h2.config import H2Configuration
from h2.connection import H2Connection
from h2_server import H2ServerConnection

import h2.connection
import handlers

HOST = '0.0.0.0'
PORT = 50051

logging.basicConfig(level=logging.INFO)


def handle_client_connection(conn, addr):
    logging.info(f"Accepted connection from {addr}")
    h2_conn = H2ServerConnection()
    conn.sendall(h2_conn.initiate_connection())

    h2_conn.set_handler("request", handlers.on_request)
    h2_conn.set_handler("data", handlers.on_data_factory(h2_conn))

    try:
        while True:
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


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    logging.info(f"gRPC test server listening on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(
                target=handle_client_connection, args=(conn, addr), daemon=True
            )
            client_thread.start()
    except KeyboardInterrupt:
        logging.info("Shutting down server")
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
