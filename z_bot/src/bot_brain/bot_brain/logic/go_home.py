"""
Go-home logic: navigate to home wall, center between tags, park parallel.
All phase logic lives here; FSM delegates to update().
"""

import math
from enum import Enum, auto
from typing import Any, Optional

from .april import ZONE_TAG_RANGES, get_home_center_tag_ids
from .command import Command
from .world_model import WorldModel, AprilTagInfo

# Arena heading for each wall (degrees): North=0, East=90, South=180, West=270
WALL_HEADING: dict[str, float] = {
    "North": 0.0,
    "East": 90.0,
    "South": 180.0,
    "West": 270.0,
}


def _normalize_angle_diff(deg_a: float, deg_b: float) -> float:
    """Angle difference in [-180, 180]."""
    return (deg_a - deg_b + 180) % 360 - 180


class GoHomePhase(Enum):
    TURN_TO_HOME = auto()
    NAVIGATE = auto()
    CENTER = auto()
    PARK_PARALLEL = auto()


class _State:
    def __init__(self):
        self.phase = GoHomePhase.TURN_TO_HOME


_state = _State()


def reset() -> None:
    """Call when transitioning to GO_HOME to reset phase."""
    _state.phase = GoHomePhase.TURN_TO_HOME


def _facing_wall(tags: list[AprilTagInfo], home_wall: str) -> bool:
    """True if we see home-wall tags (we're facing home)."""
    target_lo, target_hi = ZONE_TAG_RANGES.get(home_wall, (0, 5))
    for t in tags:
        if target_lo <= t.tag_id <= target_hi:
            return True
    return False


def _turn_toward_home(
    tags: list[AprilTagInfo],
    heading_deg: Optional[float],
    home_wall: str,
    params: Any,
) -> Command:
    """Turn to face home wall. No tags -> slow spin."""
    if not tags or heading_deg is None:
        return Command(0.0, params.GO_HOME_TURN_SPEED)

    target = WALL_HEADING.get(home_wall, 0.0)
    diff = _normalize_angle_diff(target, heading_deg)
    if abs(diff) < 15.0:
        return Command(0.0, 0.0)
    return Command(0.0, params.GO_HOME_TURN_SPEED if diff > 0 else -params.GO_HOME_TURN_SPEED)


def _center_offset(tags: list[AprilTagInfo], home_wall: str) -> Optional[float]:
    """Offset of midpoint(2,3) from image center. Positive = turn right."""
    center_lo, center_hi = get_home_center_tag_ids(home_wall)
    t2 = next((t for t in tags if t.tag_id == center_lo), None)
    t3 = next((t for t in tags if t.tag_id == center_hi), None)
    if t2 is None or t3 is None:
        return None
    mx = (t2.center_x + t3.center_x) / 2
    all_x = [t.center_x for t in tags]
    frame_cx = (min(all_x) + max(all_x)) / 2
    return mx - frame_cx


def _wall_angle_deg(tags: list[AprilTagInfo]) -> Optional[float]:
    """Angle of tag top edge in image (radians -> deg). 0 = horizontal."""
    if not tags or len(tags[0].corners) < 4:
        return None
    c0, c1 = tags[0].corners[0], tags[0].corners[1]
    dx, dy = c1[0] - c0[0], c1[1] - c0[1]
    return math.degrees(math.atan2(dy, dx))


def update(wm: WorldModel, params: Any) -> Command:
    """
    Single entry point for go-home. Returns command for current phase.
    State is internal; call reset() when entering GO_HOME.
    """
    tags = wm.april_tags or []
    range_cm = wm.range_cm
    heading = wm.heading_deg
    home_wall = wm.home_wall

    # ----- TURN_TO_HOME -----
    if _state.phase == GoHomePhase.TURN_TO_HOME:
        if _facing_wall(tags, home_wall):
            _state.phase = GoHomePhase.NAVIGATE
            return Command(0.0, 0.0)
        return _turn_toward_home(tags, heading, home_wall, params)

    # ----- NAVIGATE -----
    if _state.phase == GoHomePhase.NAVIGATE:
        if not _facing_wall(tags, home_wall):
            return _turn_toward_home(tags, heading, home_wall, params)
        if range_cm is not None and range_cm < params.NAV_CLOSE_CM:
            _state.phase = GoHomePhase.CENTER
            return Command(0.0, 0.0)
        return Command(params.GO_HOME_NAV_SPEED, 0.0)

    # ----- CENTER -----
    if _state.phase == GoHomePhase.CENTER:
        offset = _center_offset(tags, home_wall)
        if offset is None:
            return _turn_toward_home(tags, heading, home_wall, params)
        if abs(offset) < params.CENTER_EPSILON_PX:
            if range_cm is not None and range_cm < params.PARK_CLOSE_CM:
                _state.phase = GoHomePhase.PARK_PARALLEL
                return Command(0.0, 0.0)
            return Command(params.GO_HOME_NAV_SPEED, 0.0)
        speed = params.GO_HOME_TURN_SPEED if offset > 0 else -params.GO_HOME_TURN_SPEED
        return Command(0.0, speed)

    # ----- PARK_PARALLEL -----
    if _state.phase == GoHomePhase.PARK_PARALLEL:
        angle = _wall_angle_deg(tags)
        if angle is None:
            return Command(0.0, 0.0)
        if abs(angle) < params.PARALLEL_EPSILON_DEG:
            return Command(0.0, 0.0)
        k = 0.02
        return Command(0.0, -k * angle)

    return Command(0.0, 0.0)
