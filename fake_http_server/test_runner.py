import subprocess
import time
import signal
import sys
from pathlib import Path

PYTHON_EXEC = sys.executable
BASE_DIR = Path(__file__).parent.resolve()

MODES = ["length_mismatch", "invalid_stream", "unknown_type"]

def run_test(mode):
    print(f"\n[+] Running test mode: {mode}")

    server_proc = subprocess.Popen(
        [PYTHON_EXEC, str(BASE_DIR / "fake_server.py"), "--mode", mode],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    time.sleep(1.5)

    try:
        subprocess.run(
            [PYTHON_EXEC, str(BASE_DIR / "grpc_client.py"), "--test", mode],
            check=True
        )
    except subprocess.CalledProcessError:
        print(f"[!] Client test failed for mode: {mode}")

    server_proc.send_signal(signal.SIGINT)
    try:
        server_proc.wait(timeout=1)
    except subprocess.TimeoutExpired:
        server_proc.kill()

def main():
    print("[*] Starting gRPC HTTP/2 Fault Injection Test Runner")
    for mode in MODES:
        run_test(mode)
    print("[*] All tests finished. Results written to result.log")

if __name__ == "__main__":
    main()
