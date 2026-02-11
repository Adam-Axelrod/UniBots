"""
Speaker (real) — hardware stub.
"""

from output.base import Actuator


class SpeakerReal(Actuator):
    """Placeholder for real speaker/buzzer hardware."""

    def init(self) -> None:
        pass

    def beep(self) -> None:
        raise NotImplementedError("SpeakerReal.beep() not implemented yet")

    def stop(self) -> None:
        pass
