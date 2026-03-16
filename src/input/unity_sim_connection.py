"""
Shared TCP connection to Unity simulation.
Used by sim camera (frames) and sim motor (commands).
"""

import socket
import threading


class UnitySimConnection:
    """Bidirectional TCP connection to Unity. recv for frames, send_command for motor."""

    def __init__(self, host: str, port: int):
        self._host = host
        self._port = port
        self._sock: socket.socket | None = None
        self._send_lock = threading.Lock()
        self._latest_distance_m: float = 0.0

    def init(self) -> None:
        """Connect to Unity."""
        print(f"[UnitySim] Connecting to {self._host}:{self._port}")
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((self._host, self._port))
        self._sock.settimeout(0.1)
        print(f"[UnitySim] Connected to {self._host}:{self._port}")

    def update_distance(self, d_m: float) -> None:
        """Update latest ultrasonic distance (metres). Called by camera reader."""
        self._latest_distance_m = d_m

    def get_distance_cm(self) -> float:
        """Return latest ultrasonic distance in cm."""
        return self._latest_distance_m * 100.0

    def recv(self, size: int) -> bytes:
        """Read from socket. For camera reader thread."""
        if self._sock is None:
            return b""
        try:
            return self._sock.recv(size)
        except (ConnectionResetError, BrokenPipeError, OSError):
            return b""

    def send_command(self, cmd: str) -> None:
        """Send motor command to Unity. Format: cmd + newline, ASCII."""
        if self._sock is None:
            return
        with self._send_lock:
            try:
                self._sock.sendall((cmd + "\n").encode("ascii"))
            except (BrokenPipeError, ConnectionResetError, OSError) as e:
                print(f"[UnitySim] send_command failed: {e}")

    def close(self) -> None:
        """Close the connection."""
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
            print("[UnitySim] Connection closed")
