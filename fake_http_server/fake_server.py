import socket
import struct
import time
import argparse

HTTP2_PREFACE = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"

def build_invalid_length_frame():
    # 宣稱 payload 長度為 1000（實際只有 10）
    length = 1000
    frame_type = 0x0  # DATA frame
    flags = 0x0
    stream_id = 1

    header = struct.pack(">I", length << 8 | frame_type)
    header += struct.pack("B", flags)
    header += struct.pack(">I", stream_id & 0x7FFFFFFF)

    payload = b"A" * 10  # 實際 payload 遠小於 length
    return header + payload

def build_invalid_stream_id_frame():
    # stream_id = 0 對於 DATA 是非法的
    length = 5
    frame_type = 0x0  # DATA
    flags = 0x0
    stream_id = 0  # 非法

    header = struct.pack(">I", length << 8 | frame_type)
    header += struct.pack("B", flags)
    header += struct.pack(">I", stream_id)

    payload = b"12345"
    return header + payload

def build_unknown_frame_type():
    length = 0
    frame_type = 0xFF  # 不存在的 frame type
    flags = 0
    stream_id = 1

    header = struct.pack(">I", length << 8 | frame_type)
    header += struct.pack("B", flags)
    header += struct.pack(">I", stream_id)
    return header  # no payload

def get_frame_by_mode(mode):
    if mode == "length_mismatch":
        return build_invalid_length_frame()
    elif mode == "invalid_stream":
        return build_invalid_stream_id_frame()
    elif mode == "unknown_type":
        return build_unknown_frame_type()
    else:
        raise ValueError(f"Unsupported mode: {mode}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, required=True,
                        help="Test mode: length_mismatch | invalid_stream | unknown_type")
    args = parser.parse_args()

    frame = get_frame_by_mode(args.mode)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 50051))
        s.listen(1)
        print("[*] Fake HTTP/2 server listening on port 50051...")
        print(f"[*] Mode: {args.mode}")

        conn, addr = s.accept()
        with conn:
            print(f"[+] Connection from {addr}")

            # 等待 client 傳送 preface
            preface = conn.recv(24)
            print(f"[+] Received client preface: {preface}")

            # 發送錯誤 frame
            print(f"[!] Sending malformed frame ({args.mode})...")
            conn.sendall(frame)

            time.sleep(1)

if __name__ == "__main__":
    main()
