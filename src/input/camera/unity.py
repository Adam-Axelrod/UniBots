"""
Unity TCP camera (sim).
"""

import queue
import socket
import threading

import cv2
import numpy as np

from input.base import Sensor


class UnityTCPCamera(Sensor):
    """Frames from Unity over TCP. Reader thread drains socket."""

    def __init__(
        self,
        host: str,
        port: int,
        width: int,
        height: int,
        queue_maxsize: int,
        name: str = "camera",
    ):
        self._host = host
        self._port = port
        self._width = width
        self._height = height
        self._frame_size = width * height * 4
        self._queue_maxsize = queue_maxsize
        self._name = name
        self._sock: socket.socket | None = None
        self._queue: queue.Queue | None = None
        self._reader_running = False
        self._thread: threading.Thread | None = None

    def init(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((self._host, self._port))
        self._sock.settimeout(0.1)
        print(f"[Camera] Connected to Unity at {self._host}:{self._port}")
        self._queue = queue.Queue(maxsize=self._queue_maxsize)
        self._reader_running = True
        self._thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._thread.start()
        print("[Camera] Unity reader thread started")

    def _reader_loop(self) -> None:
        buffer = b""
        while self._reader_running and self._sock:
            try:
                data = self._sock.recv(65536)
                if data:
                    buffer += data
            except socket.timeout:
                pass
            except (ConnectionResetError, BrokenPipeError, OSError):
                break
            while len(buffer) >= self._frame_size and self._reader_running:
                frame_bytes = buffer[: self._frame_size]
                buffer = buffer[self._frame_size :]
                frame = np.frombuffer(frame_bytes, dtype=np.uint8)
                frame = frame.reshape((self._height, self._width, 4))
                frame = frame[:, :, :3]
                frame = cv2.flip(frame, 0)
                frame = frame.astype(np.float32) / 255.0
                frame = np.power(frame, 1.0 / 2.2)
                frame = (frame * 255.0).astype(np.uint8)
                try:
                    self._queue.put_nowait(frame)
                except queue.Full:
                    try:
                        self._queue.get_nowait()
                    except queue.Empty:
                        pass
                    self._queue.put_nowait(frame)

    def get_data(self) -> np.ndarray | None:
        if self._queue is None:
            return None
        return self._queue.get(block=True)

    def stop(self) -> None:
        self._reader_running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
