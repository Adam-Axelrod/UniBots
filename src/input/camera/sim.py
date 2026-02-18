"""
Sim camera: frames from Unity over TCP.
"""

import queue
import threading

import cv2
import numpy as np

from input.base import Sensor
from input.unity_sim_connection import UnitySimConnection


class UnityTCPCamera(Sensor):
    """Frames from Unity over TCP. Reader thread drains socket via UnitySimConnection."""

    def __init__(
        self,
        connection: UnitySimConnection,
        width: int,
        height: int,
        queue_maxsize: int,
        name: str = "camera",
    ):
        self._conn = connection
        self._width = width
        self._height = height
        self._frame_size = width * height * 4
        self._queue_maxsize = queue_maxsize
        self._name = name
        self._queue: queue.Queue | None = None
        self._reader_running = False
        self._thread: threading.Thread | None = None

    def init(self) -> None:
        """Start reader thread. Connection must already be initialized."""
        self._queue = queue.Queue(maxsize=self._queue_maxsize)
        self._reader_running = True
        self._thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._thread.start()
        print("[Camera] Unity reader thread started")

    def _reader_loop(self) -> None:
        buffer = b""
        while self._reader_running:
            try:
                data = self._conn.recv(65536)
                if data:
                    buffer += data
            except Exception:
                break
            while len(buffer) >= self._frame_size and self._reader_running:
                frame_bytes = buffer[: self._frame_size]
                buffer = buffer[self._frame_size :]
                frame = np.frombuffer(frame_bytes, dtype=np.uint8)
                frame = frame.reshape((self._height, self._width, 4))
                frame = frame[:, :, :3]
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
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
        """Stop reader thread. Does not close connection (main orchestrates)."""
        self._reader_running = False
        if self._thread:
            self._thread.join(timeout=1.0)
