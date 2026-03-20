import math
from enum import Enum, auto
from typing import Optional, Tuple

from .world_model import WorldModel
from .command import Command
from . import params
from . import go_home

STOP = Command(0.0, 0.0)


def _normalize_angle_diff(deg_a: float, deg_b: float) -> float:
    """Normalize angle difference to [-180, 180] degrees."""
    return (deg_a - deg_b + 180) % 360 - 180


def _obstacle_detected(range_cm: Optional[float]) -> bool:
    """Returns True when obstacle is closer than AVOID_DISTANCE_CM."""
    if range_cm is None or math.isnan(range_cm):
        return False
    return range_cm < params.AVOID_DISTANCE_CM


class State(Enum):
    SEARCH = auto()
    ALIGN = auto()
    DRIVE = auto()
    AVOID = auto()
    GO_HOME = auto()


class SearchPhase(Enum):
    TURN = auto()
    FORWARD = auto()


class SearchTurnSubphase(Enum):
    ROTATE = auto()
    PAUSE = auto()


class BrainFSM:

    def __init__(self):
        self.state = State.SEARCH
        self.state_before_avoid: Optional[State] = None
        self.last_cluster_seen_s: Optional[float] = None

        # Go-home state (phase machine)
        self.go_home_state = go_home.GoHomeState()

        # AVOID turn tracking
        self.turning = False
        self.turn_start_heading: Optional[float] = None

        # SEARCH phase tracking
        self.search_phase: SearchPhase = SearchPhase.TURN
        self.search_turn_start_heading: Optional[float] = None
        self.search_last_heading: Optional[float] = None
        self.search_rotation_accumulated: float = 0.0
        self.search_forward_start_s: Optional[float] = None

        # Chunked turn: rotate N deg, pause, repeat
        self.search_turn_subphase: SearchTurnSubphase = SearchTurnSubphase.ROTATE
        self.search_chunk_start_heading: Optional[float] = None
        self.search_chunk_accumulated: float = 0.0
        self.search_pause_end_s: Optional[float] = None

    def _reset_search_phase(self) -> None:
        self.search_phase = SearchPhase.TURN
        self.search_turn_start_heading = None
        self.search_last_heading = None
        self.search_rotation_accumulated = 0.0
        self.search_forward_start_s = None
        self.search_turn_subphase = SearchTurnSubphase.ROTATE
        self.search_chunk_start_heading = None
        self.search_chunk_accumulated = 0.0
        self.search_pause_end_s = None

    def update(self, wm: WorldModel) -> Tuple[State, Command]:
        # Obstacle check: trigger AVOID from any state
        if _obstacle_detected(wm.range_cm):
            if self.state != State.AVOID:
                self.state_before_avoid = self.state
            self.state = State.AVOID
            self.turning = False

        if wm.cluster is not None:
            self.last_cluster_seen_s = wm.now_s

        handlers = {
            State.SEARCH: self._update_search,
            State.ALIGN: self._update_align,
            State.DRIVE: self._update_drive,
            State.AVOID: self._update_avoid,
            State.GO_HOME: self._update_go_home,
        }
        return handlers.get(self.state, self._fallback)(wm)

    def _update_search(self, wm: WorldModel) -> Tuple[State, Command]:
        # Cluster seen → ALIGN (from any phase)
        if wm.cluster is not None:
            self._reset_search_phase()
            self.state = State.ALIGN
            return self.state, STOP

        if self.search_phase == SearchPhase.TURN:
            # Start turn phase
            if self.search_turn_start_heading is None and wm.heading_deg is not None:
                self.search_turn_start_heading = wm.heading_deg
                self.search_last_heading = wm.heading_deg
                self.search_rotation_accumulated = 0.0
                self.search_chunk_start_heading = wm.heading_deg
                self.search_chunk_accumulated = 0.0

            # Pause subphase: stop for YOLO detection window
            if self.search_turn_subphase == SearchTurnSubphase.PAUSE:
                if wm.now_s >= (self.search_pause_end_s or 0):
                    if self.search_rotation_accumulated >= params.SEARCH_TURN_ANGLE_DEG:
                        self._reset_search_phase()
                        self.search_phase = SearchPhase.FORWARD
                        self.search_forward_start_s = wm.now_s
                        return self.state, STOP
                    self.search_turn_subphase = SearchTurnSubphase.ROTATE
                    self.search_chunk_start_heading = wm.heading_deg
                    self.search_chunk_accumulated = 0.0
                return self.state, STOP

            # Rotate subphase: turn until chunk complete
            if wm.heading_deg is not None and self.search_last_heading is not None:
                delta = _normalize_angle_diff(wm.heading_deg, self.search_last_heading)
                self.search_rotation_accumulated += abs(delta)
                self.search_chunk_accumulated += abs(delta)
                self.search_last_heading = wm.heading_deg

                if self.search_chunk_accumulated >= params.SEARCH_TURN_CHUNK_DEG:
                    self.search_turn_subphase = SearchTurnSubphase.PAUSE
                    self.search_pause_end_s = wm.now_s + params.SEARCH_TURN_PAUSE_S
                    return self.state, STOP

                if self.search_rotation_accumulated >= params.SEARCH_TURN_ANGLE_DEG:
                    self._reset_search_phase()
                    self.search_phase = SearchPhase.FORWARD
                    self.search_forward_start_s = wm.now_s
                    return self.state, STOP

            return self.state, Command(0.0, params.SEARCH_TURN_SPEED)

        # search_phase == SearchPhase.FORWARD
        if self.search_forward_start_s is None:
            self.search_forward_start_s = wm.now_s

        if wm.now_s - self.search_forward_start_s >= params.SEARCH_DRIVE_S:
            self._reset_search_phase()
            return self.state, STOP

        return self.state, Command(params.SEARCH_FORWARD_SPEED, 0.0)

    def _update_avoid(self, wm: WorldModel) -> Tuple[State, Command]:
        # Early exit when obstacle clears
        if not _obstacle_detected(wm.range_cm):
            self.turning = False
            self._reset_search_phase()
            if wm.should_go_home:
                self.state = State.GO_HOME
                self.enter_go_home()
            else:
                self.state = self.state_before_avoid or State.SEARCH
            self.state_before_avoid = None
            return self.state, STOP

        # Start turn once
        if not self.turning:
            self.turning = True
            self.turn_start_heading = wm.heading_deg

        if wm.heading_deg is not None and self.turn_start_heading is not None:
            delta = _normalize_angle_diff(wm.heading_deg, self.turn_start_heading)
            if abs(delta) < params.AVOID_TURN_ANGLE_DEG:
                return self.state, Command(0.0, params.AVOID_TURN_SPEED)

            self.turning = False
            self._reset_search_phase()
            self.state = State.SEARCH
            return self.state, STOP

        return self.state, Command(0.0, params.AVOID_TURN_SPEED)

    def _update_align(self, wm: WorldModel) -> Tuple[State, Command]:
        if wm.cluster is None:
            if self.last_cluster_seen_s is not None and wm.now_s - self.last_cluster_seen_s < params.ALIGN_LOST_GRACE_S:
                return self.state, STOP
            self._reset_search_phase()
            self.state = State.SEARCH
            return self.state, STOP

        side = wm.cluster.side
        if abs(side) < params.SIDE_EPSILON:
            self.state = State.DRIVE
            return self.state, STOP

        if side > 0:
            return self.state, Command(0.0, params.ALIGN_SPEED)
        return self.state, Command(0.0, -params.ALIGN_SPEED)

    def _update_drive(self, wm: WorldModel) -> Tuple[State, Command]:
        if wm.cluster is None:
            if self.last_cluster_seen_s is not None and wm.now_s - self.last_cluster_seen_s < params.DRIVE_LOST_GRACE_S:
                return self.state, STOP
            self._reset_search_phase()
            self.state = State.SEARCH
            return self.state, STOP

        if abs(wm.cluster.side) >= params.SIDE_EPSILON:
            self.state = State.ALIGN
            return self.state, STOP

        return self.state, Command(params.DRIVE_SPEED, 0.0)

    def _update_go_home(self, wm: WorldModel) -> Tuple[State, Command]:
        cmd = go_home.update(wm, params, self.go_home_state)
        return self.state, cmd

    def enter_go_home(self) -> None:
        """Call when transitioning to GO_HOME to reset phase state."""
        self.go_home_state.phase = go_home.GoHomePhase.TURN_TO_HOME
        self.go_home_state.turn_start_heading = None
        self.go_home_state.last_tags_seen_s = None

    def _fallback(self, wm: WorldModel) -> Tuple[State, Command]:
        self.state = State.SEARCH
        return self.state, STOP
