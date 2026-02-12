"""
TCP stream frame sink: JPEG frames to viewer; reconnects on disconnect.
Non-blocking: main loop never blocks on send. Worker thread handles I/O.
"""

import queue
import socket
import threading

import cv2
import numpy as np

from debugger.base import FrameSink


class TCPStreamSink(FrameSink):
    """Stream JPEG frames to viewer over TCP. Non-blocking; worker handles I/O."""

    def __init__(
        self,
        port: int,
        send_every_n_frames: int = 2,
        jpeg_quality: int = 85,
    ):
        self._port = port
        self._send_every_n = send_every_n_frames
        self._jpeg_quality = jpeg_quality
        self._server: socket.socket | None = None
        self._client: socket.socket | None = None
        self._frame_count = 0
        self._queue: queue.Queue[np.ndarray | None] = queue.Queue(maxsize=2)
        self._worker: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind(("0.0.0.0", self._port))
        self._server.listen(1)
        self._server.settimeout(1.0)
        print(f"[Debugger] Listening for viewer on port {self._port}")
        self._try_accept()
        self._stop.clear()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()
        print("[Debugger] Worker started (non-blocking)")

    def _try_accept(self) -> bool:
        """Accept a client if one is waiting. Returns True if connected."""
        try:
            self._client, _ = self._server.accept()
            self._client.settimeout(0.5)
            print("[Debugger] Viewer connected")
            return True
        except socket.timeout:
            return False
        except OSError:
            return False

    def _worker_loop(self) -> None:
        """Worker: get frames from queue, encode, send. Reconnect on disconnect."""
        while not self._stop.is_set():
            try:
                frame = self._queue.get(timeout=0.1)
                if frame is None:
                    break
                if self._client is None:
                    if not self._try_accept():
                        continue
                self._frame_count += 1
                if self._frame_count % self._send_every_n != 0:
                    continue
                jpeg = cv2.imencode(
                    ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, self._jpeg_quality]
                )[1]
                data = jpeg.tobytes()
                self._client.sendall(len(data).to_bytes(4, "big") + data)
            except queue.Empty:
                continue
            except (BrokenPipeError, ConnectionResetError, OSError):
                print("[Debugger] Viewer disconnect, reconnecting...")
                try:
                    if self._client:
                        self._client.close()
                except OSError:
                    pass
                self._client = None

    def send(self, frame: np.ndarray) -> bool:
        """Enqueue frame and return immediately. Never blocks main loop."""
        try:
            self._queue.put_nowait(frame)
        except queue.Full:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self._queue.put_nowait(frame)
            except queue.Full:
                pass
        return False

    def close(self) -> None:
        self._stop.set()
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        if self._worker:
            self._worker.join(timeout=2.0)
            self._worker = None
        if self._client:
            try:
                self._client.close()
            except OSError:
                pass
            self._client = None
        if self._server:
            self._server.close()
            self._server = None
