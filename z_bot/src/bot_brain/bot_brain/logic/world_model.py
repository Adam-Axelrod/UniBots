from dataclasses import dataclass
from typing import Optional


@dataclass
class AprilTagInfo:
    tag_id: int
    center_x: float
    center_y: float
    area: float
    corners: list[tuple[float, float]]


@dataclass
class ClusterInfo:
    side: float          # -1 left, 0 centered, +1 right
    cx: float            # pixels (0..width)
    cy: float            # pixels (0..height)
    count: float         # balls in major cluster
    num_clusters: float  # total clusters


@dataclass
class WorldModel:
    # Sensors
    range_cm: Optional[float] = None
    cluster: Optional[ClusterInfo] = None

    # Compass heading (0..360). Optional for now.
    heading_deg: Optional[float] = None

    # AprilTag detections (for go-home)
    april_tags: Optional[list[AprilTagInfo]] = None

    # Home wall for go-home (North, South, East, West)
    home_wall: str = "North"

    # True when it's time to go home (elapsed >= RUN_TIME - trigger)
    should_go_home: bool = False

    # Timing
    now_s: float = 0.0
    elapsed_s: float = 0.0
