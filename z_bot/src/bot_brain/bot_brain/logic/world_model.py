from dataclasses import dataclass
from typing import Optional


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

    # Timing
    now_s: float = 0.0
    elapsed_s: float = 0.0
