"""
Speaker (sim) — no-op beep.
"""

from output.base import Actuator


class SpeakerSim(Actuator):
    """Sim speaker. beep() is a no-op."""

    def init(self) -> None:
        pass

    def beep(self) -> None:
        pass

    def stop(self) -> None:
        pass
