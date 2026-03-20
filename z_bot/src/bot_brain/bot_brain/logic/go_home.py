"""
Go-home logic: navigate to home wall, center between tags, park parallel.
All phase logic lives here; FSM delegates to update().
"""

import math
from enum import Enum, auto
from typing import Any, Optional

from .april import ZONE_TAG_RANGES, get_home_center_tag_ids, wall_from_tag_id
from .command import Command
from .world_model import WorldModel, AprilTagInfo

class GoHomePhase(Enum):
    TURN_TO_HOME = auto()
    NAVIGATE = auto()
    CENTER = auto()
    ALIGN_PARALLEL = auto()
    APPROACH_WALL = auto()


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


def _tag_sequence(tags: list[AprilTagInfo]) -> list[tuple[int, str]]:
    """Sort tags by center_x (left-to-right in image), return [(tag_id, wall), ...]."""
    sorted_tags = sorted(tags, key=lambda t: t.center_x)
    result: list[tuple[int, str]] = []
    for t in sorted_tags:
        wall = wall_from_tag_id(t.tag_id)
        if wall is not None:
            result.append((t.tag_id, wall))
    return result


def _infer_facing_from_sequence(tags: list[AprilTagInfo]) -> Optional[str]:
    """Infer primary facing wall from tag sequence. Single wall -> that wall;
    two walls -> pick by tag count, then area, then leftmost in image."""
    if not tags:
        return None
    seq = _tag_sequence(tags)
    if not seq:
        return None
    walls_seen: set[str] = {w for _, w in seq}
    if len(walls_seen) == 1:
        return next(iter(walls_seen))
    # Two or more walls: pick dominant by tag count, then total area
    wall_counts: dict[str, int] = {}
    wall_area: dict[str, float] = {}
    for t in tags:
        w = wall_from_tag_id(t.tag_id)
        if w is not None:
            wall_counts[w] = wall_counts.get(w, 0) + 1
            wall_area[w] = wall_area.get(w, 0.0) + t.area
    best = max(wall_counts, key=lambda w: (wall_counts[w], wall_area.get(w, 0)))
    return best


# (facing_wall, home_wall) -> turn direction: -1 left, +1 right, 0 done
# Adjacent: N<->E, E<->S, S<->W, W<->N. Opposite: N<->S, E<->W.
_TURN_TABLE: dict[tuple[str, str], int] = {
    ("North", "North"): 0,
    ("North", "East"): 1,
    ("North", "South"): 1,
    ("North", "West"): -1,
    ("East", "North"): -1,
    ("East", "East"): 0,
    ("East", "South"): 1,
    ("East", "West"): 1,
    ("South", "North"): 1,
    ("South", "East"): -1,
    ("South", "South"): 0,
    ("South", "West"): 1,
    ("West", "North"): 1,
    ("West", "East"): 1,
    ("West", "South"): -1,
    ("West", "West"): 0,
}


def _turn_direction_toward_home(facing_wall: str, home_wall: str) -> int:
    """Return -1 (turn left), +1 (turn right), or 0 (done)."""
    return _TURN_TABLE.get((facing_wall, home_wall), 0)


def _turn_toward_home(
    tags: list[AprilTagInfo],
    home_wall: str,
    params: Any,
) -> Command:
    """Turn to face home wall using tag sequence. No tags -> slow spin."""
    if not tags:
        return Command(0.0, params.GO_HOME_TURN_SPEED)

    target_lo, target_hi = ZONE_TAG_RANGES.get(home_wall, (0, 5))
    home_tags = [t for t in tags if target_lo <= t.tag_id <= target_hi]

    if home_tags:
        # Home tags visible: use centroid offset
        centroid_x = sum(t.center_x for t in home_tags) / len(home_tags)
        all_x = [t.center_x for t in tags]
        frame_cx = (min(all_x) + max(all_x)) / 2
        offset = centroid_x - frame_cx
        if abs(offset) < params.CENTER_EPSILON_PX:
            return Command(0.0, 0.0)
        speed = params.GO_HOME_TURN_SPEED if offset > 0 else -params.GO_HOME_TURN_SPEED
        return Command(0.0, speed)

    # Only non-home tags: infer facing from sequence and use turn table
    facing = _infer_facing_from_sequence(tags)
    if facing is None:
        return Command(0.0, params.GO_HOME_TURN_SPEED)
    d = _turn_direction_toward_home(facing, home_wall)
    return Command(0.0, float(d) * params.GO_HOME_TURN_SPEED)


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


def _clamp_speed(v: float, min_speed: float) -> float:
    """Clamp non-zero speed to at least min_speed so motor responds."""
    if v == 0:
        return 0.0
    return max(min_speed, abs(v)) * (1 if v > 0 else -1)


def update(wm: WorldModel, params: Any) -> Command:
    """
    Single entry point for go-home. Returns command for current phase.
    State is internal; call reset() when entering GO_HOME.
    """
    tags = wm.april_tags or []
    range_cm = wm.range_cm
    home_wall = wm.home_wall

    # ----- TURN_TO_HOME -----
    if _state.phase == GoHomePhase.TURN_TO_HOME:
        if _facing_wall(tags, home_wall):
            _state.phase = GoHomePhase.NAVIGATE
            return Command(0.0, 0.0)
        return _turn_toward_home(tags, home_wall, params)

    # ----- NAVIGATE -----
    if _state.phase == GoHomePhase.NAVIGATE:
        if not _facing_wall(tags, home_wall):
            return _turn_toward_home(tags, home_wall, params)
        if range_cm is not None and range_cm < params.NAV_CLOSE_CM:
            _state.phase = GoHomePhase.CENTER
            return Command(0.0, 0.0)
        return Command(params.GO_HOME_NAV_SPEED, 0.0)

    # ----- CENTER -----
    if _state.phase == GoHomePhase.CENTER:
        offset = _center_offset(tags, home_wall)
        if offset is None:
            return _turn_toward_home(tags, home_wall, params)
        if abs(offset) < params.CENTER_EPSILON_PX:
            if range_cm is not None and range_cm < params.NAV_CLOSE_CM:
                _state.phase = GoHomePhase.ALIGN_PARALLEL
                return Command(0.0, 0.0)
            return Command(params.GO_HOME_NAV_SPEED, 0.0)
        speed = params.GO_HOME_TURN_SPEED if offset > 0 else -params.GO_HOME_TURN_SPEED
        return Command(0.0, speed)

    # ----- ALIGN_PARALLEL -----
    if _state.phase == GoHomePhase.ALIGN_PARALLEL:
        angle = _wall_angle_deg(tags)
        if angle is None or abs(angle) < params.PARALLEL_EPSILON_DEG:
            _state.phase = GoHomePhase.APPROACH_WALL
            return Command(0.0, 0.0)
        k = 0.02
        angular = _clamp_speed(-k * angle, params.MIN_MOTOR_SPEED)
        return Command(0.0, angular)

    # ----- APPROACH_WALL -----
    if _state.phase == GoHomePhase.APPROACH_WALL:
        if range_cm is None or range_cm < params.PARK_CLOSE_CM:
            return Command(0.0, 0.0)
        return Command(params.GO_HOME_NAV_SPEED, 0.0)

    return Command(0.0, 0.0)
