import struct
import logging

import messages_pb2


def on_request(event, stream_id):
    logging.info(f"→ [gRPC] request headers received (stream={stream_id})")


def on_data_factory(h2_conn):
    def on_data(event, stream_id):
        data = h2_conn.stream_data[stream_id]
        if len(data) < 5:
            return  # wait for full gRPC header (1 + 4 bytes)

        # Extract gRPC message length
        compressed_flag = data[0]
        msg_len = struct.unpack(">I", data[1:5])[0]
        if len(data) < 5 + msg_len:
            return  # wait for full message body

        # Extract protobuf message
        msg_bytes = data[5:5 + msg_len]
        req = messages_pb2.SimpleRequest()
        req.ParseFromString(msg_bytes)

        logging.info(f"→ [gRPC] received request: response_size={req.response_size}")


        resp = messages_pb2.SimpleResponse()
        resp.payload.body = b'\x42' * req.response_size
        h2_conn.send_response(stream_id, resp.SerializeToString())

    return on_data
