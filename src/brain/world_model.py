"""
World model: brain's view of the world, updated each loop from sensors and vision.
"""

from dataclasses import dataclass, field


@dataclass
class WorldModel:
    """Aggregates all inputs; derived fields for FSM decisions."""

    # From vision (VisionModule)
    ball_detected: bool = False
    ball_centers: list[tuple[int, int]] = field(default_factory=list)
    target_ball: tuple[int, int] | None = None  # nearest or path-first

    # From ultrasonic
    distance_cm: float = 0.0
    obstacle: bool = False

    # From encoders
    encoder_left: int = 0
    encoder_right: int = 0

    # From IMU
    heading: float | None = None

    # From rear camera (when used)
    wall_visible: bool = False

    # Derived / game state
    time_remaining: float = 0.0
    time_low: bool = False
    ball_lost: bool = False
    obstacle_cleared: bool = False
    start_signal: bool = False
