"""
Debugger interface for annotated frame viewing.
"""

from abc import ABC, abstractmethod

import numpy as np


class FrameSink(ABC):
    """
    Debug frame viewer. start() -> send(frame) in loop -> close().

    send(frame) returns bool: True if user requested quit.
    """

    @abstractmethod
    def start(self) -> None:
        """Start the frame sink. Call before send()."""
        ...

    @abstractmethod
    def send(self, frame: np.ndarray) -> bool:
        """Send frame. Returns True if user requested quit."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Release resources. Call when done."""
        ...
