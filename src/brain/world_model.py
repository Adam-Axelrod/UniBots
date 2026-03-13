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

    # Homing
    home_tag_visible: bool = False
    home_tag_center: tuple[int, int] | None = None  # pixel coords in frame
    home_tag_id: int | None = None
    home_tag_area: float = 0.0
    home_tag_centered: bool = False  # tag within margin of frame center
    home_tag_align_centered: bool = False  # tag within smaller margin for drop
    home_tag_left_of_center: bool = False  # when not centered: True=turn LEFT
    home_wall_visible: bool = False  # wall color matches home zone
    at_home: bool = False  # home tag large + ultrasonic close
    at_home_center: bool = False  # at_home and visible tag is center (e.g. 2 or 3 for North)
    home_center_tag_lo: int | None = None  # center tag range for along-wall steering
    home_center_tag_hi: int | None = None
