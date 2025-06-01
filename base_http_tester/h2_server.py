import h2.connection
import h2.events
import struct
import logging
from h2.config import H2Configuration
import h2.connection
from time import sleep
class H2ServerConnection:
    def __init__(self):
        config = H2Configuration(client_side=False)
        self.conn = h2.connection.H2Connection(config=config)
        self.handlers = {
            "request": self._default_on_request,
            "data": self._default_on_data,
        }
        self.stream_data = {}

    def initiate_connection(self):
        self.conn.initiate_connection()
        return self.conn.data_to_send()

    def receive_data(self, data):
        """Feed raw TCP data into the h2 connection."""
        events = self.conn.receive_data(data)
        responses = []

        for event in events:
            if isinstance(event, h2.events.RequestReceived):
                stream_id = event.stream_id
                self.stream_data[stream_id] = b""
                self.handlers["request"](event, stream_id)

            elif isinstance(event, h2.events.DataReceived):
                stream_id = event.stream_id
                self.stream_data[stream_id] += event.data
                self.conn.acknowledge_received_data(len(event.data), stream_id)
                self.handlers["data"](event, stream_id)

            elif isinstance(event, h2.events.WindowUpdated):
                pass  # Not implemented yet

        return self.conn.data_to_send()

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
            headers=[("grpc-status", "0"), ("grpc-message", "Haha")],
            end_stream=True,
        )

    def set_handler(self, event_name, handler_func):
        self.handlers[event_name] = handler_func

    def _default_on_request(self, event, stream_id):
        logging.info(f"[default] RequestReceived: stream {stream_id}")

    def _default_on_data(self, event, stream_id):
        logging.info(f"[default] DataReceived: stream {stream_id}")

    def data_to_send(self):
        return self.conn.data_to_send()
