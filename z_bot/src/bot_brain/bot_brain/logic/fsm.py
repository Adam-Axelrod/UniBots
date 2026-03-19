import math
from enum import Enum, auto
from typing import Optional, Tuple

from .world_model import WorldModel
from .command import Command
from . import params


def _obstacle_detected(range_cm: Optional[float]) -> bool:
    if range_cm is None or math.isnan(range_cm):
        return False
    return range_cm < 6   # 60 mm = 6 cm


class State(Enum):
    SEARCH = auto()
    ALIGN = auto()
    DRIVE = auto()
    AVOID = auto()


class BrainFSM:

    def __init__(self):
        self.state = State.SEARCH
        self.last_cluster_seen_s: Optional[float] = None

        # AVOID turn tracking
        self.turning = False
        self.turn_start_heading: Optional[float] = None

        # SEARCH phase tracking
        self.search_phase: str = 'turn'  # 'turn' | 'forward'
        self.search_turn_start_heading: Optional[float] = None
        self.search_last_heading: Optional[float] = None
        self.search_rotation_accumulated: float = 0.0
        self.search_forward_start_s: Optional[float] = None

    def _reset_search_phase(self) -> None:
        print(f"reset search phase")
        self.search_phase = 'turn'
        self.search_turn_start_heading = None
        self.search_last_heading = None
        self.search_rotation_accumulated = 0.0
        self.search_forward_start_s = None

    def update(self, wm: WorldModel) -> Tuple[State, Command]:

        # 🔴 Trigger AVOID ONLY from SEARCH
        if _obstacle_detected(wm.range_cm):
            self.state = State.AVOID
            self.turning = False
            return self.state, Command(0.0, 0.0)

        # Track last time ball seen
        if wm.cluster is not None:
            self.last_cluster_seen_s = wm.now_s

        # =================================
        # SEARCH
        # =================================
        if self.state == State.SEARCH:

            # Cluster seen → ALIGN (from any phase)
            if wm.cluster is not None:
                self._reset_search_phase()
                self.state = State.ALIGN
                return self.state, Command(0.0, 0.0)

            print(f"search phase: {self.search_phase}, turn start heading: {self.search_turn_start_heading}, last heading: {self.search_last_heading}, rotation accumulated: {self.search_rotation_accumulated}")

            if self.search_phase == 'turn':
                # Start turn phase
                if self.search_turn_start_heading is None and wm.heading_deg is not None:
                    self.search_turn_start_heading = wm.heading_deg
                    self.search_last_heading = wm.heading_deg
                    self.search_rotation_accumulated = 0.0

                if wm.heading_deg is not None and self.search_last_heading is not None:
                    delta = (wm.heading_deg - self.search_last_heading + 180) % 360 - 180
                    self.search_rotation_accumulated += abs(delta)
                    self.search_last_heading = wm.heading_deg

                    if abs(self.search_rotation_accumulated) >= params.SEARCH_TURN_ANGLE_DEG:
                        self._reset_search_phase()
                        self.search_phase = 'forward'
                        self.search_forward_start_s = wm.now_s
                        return self.state, Command(0.0, 0.0)

                # Keep turning left (fallback: timed turn if no IMU)
                return self.state, Command(0.0, 0.3)

            # search_phase == 'forward'
            if self.search_forward_start_s is None:
                self.search_forward_start_s = wm.now_s

            if wm.now_s - self.search_forward_start_s >= params.SEARCH_DRIVE_S:
                self._reset_search_phase()
                return self.state, Command(0.0, 0.0)

            return self.state, Command(0.2, 0.0)  # forward

        # =================================
        # AVOID (90° RIGHT TURN using IMU)
        # =================================
        if self.state == State.AVOID:

            # Start turn once
            if not self.turning:
                self.turning = True
                self.turn_start_heading = wm.heading_deg

            # If heading available
            if wm.heading_deg is not None and self.turn_start_heading is not None:

                delta = wm.heading_deg - self.turn_start_heading

                # Normalize to [-180, 180]
                delta = (delta + 180) % 360 - 180

                # Keep turning RIGHT
                if abs(delta) < 90:
                    return self.state, Command(0.0, -0.4)

                # Done turning → go back to SEARCH
                self.turning = False
                self._reset_search_phase()
                self.state = State.SEARCH
                return self.state, Command(0.0, 0.0)

            # fallback if no IMU
            return self.state, Command(0.0, -0.4)

        # =================================
        # ALIGN
        # =================================
        align_speed = 2.0
        if self.state == State.ALIGN:

            if wm.cluster is None:
                self._reset_search_phase()
                self.state = State.SEARCH
                return self.state, Command(0.0, 0.0)

            side = wm.cluster.side

            if side == 0.0:
                self.state = State.DRIVE
                return self.state, Command(0.0, 0.0)

            if side > 0:
                return self.state, Command(0.0, align_speed)

            if side < 0:
                return self.state, Command(0.0, -align_speed)

        # =================================
        # DRIVE
        # =================================
        if self.state == State.DRIVE:
            if wm.cluster is None:
                self._reset_search_phase()
                self.state = State.SEARCH
                return self.state, Command(0.0, 0.0)
            else:
                if wm.cluster.side != 0.0:
                    self.state = State.ALIGN
                    return self.state, Command(0.0, 0.0)

            return self.state, Command(0.8, 0.0)

        # =================================
        # FALLBACK
        # =================================
        self.state = State.SEARCH
        return self.state, Command(0.0, 0.0)
