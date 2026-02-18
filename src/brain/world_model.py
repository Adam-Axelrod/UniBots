"""
World model: brain's view of the world, updated each loop from sensors and vision.
"""

from dataclasses import dataclass


@dataclass
class WorldModel:
    """Aggregates inputs required for FSM decisions."""

    # Vision
    ball_detected: bool = False
    target_ball: tuple[int, int] | None = None
    ball_lost: bool = False

    # Ultrasonic
    obstacle: bool = False
    obstacle_cleared: bool = False

    # Game state
    time_low: bool = False
    wall_visible: bool = False
    start_signal: bool = False
