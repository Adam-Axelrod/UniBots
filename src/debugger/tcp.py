"""
TCP stream frame sink: JPEG frames to viewer; reconnects on disconnect.
"""

import socket

import cv2
import numpy as np

from debugger.base import FrameSink


class TCPStreamSink(FrameSink):
    """Stream JPEG frames to viewer over TCP. Reconnects on disconnect."""

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

    def start(self) -> None:
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind(("0.0.0.0", self._port))
        self._server.listen(1)
        print(f"[Debugger] Listening for viewer on port {self._port}")
        print("[Debugger] Waiting for viewer to connect...")
        self._client, _ = self._server.accept()
        self._client.settimeout(0.5)
        print("[Debugger] Viewer connected")

    def send(self, frame: np.ndarray) -> bool:
        self._frame_count += 1
        if self._frame_count % self._send_every_n != 0:
            return False
        try:
            jpeg = cv2.imencode(
                ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, self._jpeg_quality]
            )[1]
            data = jpeg.tobytes()
            self._client.sendall(len(data).to_bytes(4, "big") + data)
            return False
        except (BrokenPipeError, ConnectionResetError, OSError):
            print("[Debugger] Viewer disconnected. Waiting for reconnect...")
            try:
                if self._client:
                    self._client.close()
            except OSError:
                pass
            if self._server:
                self._client, _ = self._server.accept()
                self._client.settimeout(0.5)
                print("[Debugger] Viewer reconnected")
            return False

    def close(self) -> None:
        if self._client:
            try:
                self._client.close()
            except OSError:
                pass
            self._client = None
        if self._server:
            self._server.close()
            self._server = None
