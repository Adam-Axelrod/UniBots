"""
Viewer for YOLO stream (headless mode).
Run on your PC: connects to the TCP stream and displays annotated frames.

Usage:
  python src/debugger/viewer.py [HOST] [PORT]
  e.g. python src/debugger/viewer.py 192.168.1.100 6001
"""

import argparse
import socket
import struct
import time

import cv2
import numpy as np

# Defaults (override via command line)
DEFAULT_HOST = "192.168.137.202"
DEFAULT_PORT = 6001

# Longer timeout so temporary stalls (e.g. YOLO busy) don't disconnect
SOCKET_TIMEOUT_SEC = 30.0
RECONNECT_DELAY_SEC = 2.0

WINDOW_NAME = "YOLO Stream (viewer)"

# Poll socket in short chunks so we can check for 'q' often
RECV_POLL_TIMEOUT_SEC = 0.1


def recv_exact(sock, n, check_quit):
    """
    Read exactly n bytes. check_quit() is called while waiting.
    Returns (buf, None) on success, (None, "quit") when user pressed q,
    (None, "closed") when connection closed.
    """
    buf = b""
    while len(buf) < n:
        try:
            chunk = sock.recv(n - len(buf))
        except TimeoutError:
            chunk = None
        if chunk is not None:
            if not chunk:
                return (None, "closed")
            buf += chunk
        if len(buf) < n and check_quit():
            return (None, "quit")
    return (buf, None)


def run_viewer_loop(sock):
    """Receive and display frames. Returns when connection is lost or user quits."""
    sock.settimeout(RECV_POLL_TIMEOUT_SEC)

    fps_frame_times = []
    fps_window = 30  # average over last N frames

    while True:
        def check_quit():
            return cv2.waitKey(1) & 0xFF == ord("q")

        len_buf, reason = recv_exact(sock, 4, check_quit)
        if reason:
            return reason
        size = struct.unpack(">I", len_buf)[0]
        if size == 0 or size > 10 * 1024 * 1024:
            return "invalid_size"

        data, reason = recv_exact(sock, size, check_quit)
        if reason:
            return reason

        frame = np.frombuffer(data, dtype=np.uint8)
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
        if frame is None:
            continue

        # FPS counter
        now = time.perf_counter()
        fps_frame_times.append(now)
        if len(fps_frame_times) > fps_window:
            fps_frame_times.pop(0)
        if len(fps_frame_times) >= 2:
            elapsed = fps_frame_times[-1] - fps_frame_times[0]
            fps = (len(fps_frame_times) - 1) / elapsed if elapsed > 0 else 0
            fps_text = f"FPS: {fps:.1f}"
            cv2.putText(
                frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
            )

        cv2.imshow(WINDOW_NAME, frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            return "quit"


def main():
    parser = argparse.ArgumentParser(description="View YOLO stream (headless)")
    parser.add_argument("host", nargs="?", default=DEFAULT_HOST, help="Host IP")
    parser.add_argument("port", nargs="?", type=int, default=DEFAULT_PORT, help="Port")
    args = parser.parse_args()

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

    while True:
        print(f"Connecting to {args.host}:{args.port}...")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(SOCKET_TIMEOUT_SEC)
            sock.connect((args.host, args.port))
            print("Connected. Press 'q' to quit.")
            result = run_viewer_loop(sock)
            sock.close()
            if result == "quit":
                break
            msg = "Timeout." if result == "timeout" else "Connection lost."
            print("{} Reconnecting in {:.0f}s...".format(msg, RECONNECT_DELAY_SEC))
            time.sleep(RECONNECT_DELAY_SEC)
        except (socket.timeout, TimeoutError, ConnectionRefusedError, OSError) as e:
            print(
                "Connection failed: {}. Retrying in {:.0f}s...".format(
                    e, RECONNECT_DELAY_SEC
                )
            )
            time.sleep(RECONNECT_DELAY_SEC)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
