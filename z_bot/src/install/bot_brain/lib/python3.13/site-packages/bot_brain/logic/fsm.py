from enum import Enum, auto
from typing import Optional, Tuple

from .world_model import WorldModel
from .command import Command
from . import params


def wrap_180(deg: float) -> float:
    return (deg + 180.0) % 360.0 - 180.0


class State(Enum):
    SEARCH = auto()
    ALIGN = auto()
    DRIVE = auto()
    AVOID = auto()
    GO_HOME = auto()   # included for later; prints only for now


class BrainFSM:
    def __init__(self):
        self.state = State.SEARCH

        # Drive tracking
        self.drive_started_s: Optional[float] = None
        self.last_cluster_seen_s: Optional[float] = None

        # Go-home tracking
        self.go_home_started_s: Optional[float] = None

    def _obstacle_now(self, wm: WorldModel) -> bool:
        return wm.range_cm is not None and wm.range_cm < params.AVOID_DISTANCE_CM

    def _obstacle_clear(self, wm: WorldModel) -> bool:
        return wm.range_cm is not None and wm.range_cm >= (params.AVOID_DISTANCE_CM + params.AVOID_CLEAR_HYST_CM)

    def update(self, wm: WorldModel) -> Tuple[State, Command]:
        """
        Returns (state, command). For now command isn't used for motors,
        but we keep it for future /cmd_vel.
        """

        # ---- Timer-based switch to GO_HOME (later) ----
        if wm.elapsed_s >= params.RUN_TIME_S and self.state != State.GO_HOME:
            self.state = State.GO_HOME
            self.go_home_started_s = wm.now_s

        # ---- Avoidance has highest priority ----
        if self._obstacle_now(wm):
            self.state = State.AVOID
            return self.state, Command(0.0, 0.0)

        if self.state == State.AVOID and self._obstacle_clear(wm):
            # resume mission loop
            self.state = State.ALIGN if wm.cluster is not None else State.SEARCH

        # ---- Track last time we saw cluster ----
        if wm.cluster is not None:
            self.last_cluster_seen_s = wm.now_s

        # ---- GO_HOME (print-only for now) ----
        if self.state == State.GO_HOME:
            return self.state, Command(0.0, 0.0)

        # ---- SEARCH: rotate until cluster appears ----
        if self.state == State.SEARCH:
            if wm.cluster is not None:
                self.state = State.ALIGN
                return self.state, Command(0.0, 0.0)
            return self.state, Command(0.0, 0.0)

        # ---- ALIGN: turn until side == 0, then DRIVE ----
        if self.state == State.ALIGN:
            if wm.cluster is None:
                if params.SEARCH_WHEN_NO_CLUSTER:
                    self.state = State.SEARCH
                return self.state, Command(0.0, 0.0)

            if wm.cluster.side == 0.0:
                self.state = State.DRIVE
                self.drive_started_s = wm.now_s
                return self.state, Command(0.0, 0.0)

            # still aligning
            return self.state, Command(0.0, 0.0)

        # ---- DRIVE: keep driving until cy is low or cluster disappears briefly ----
        if self.state == State.DRIVE:
            if wm.cluster is not None:
                if wm.cluster.cy >= params.DRIVE_STOP_CY_PX:
                    # collected -> go back to ALIGN/SEARCH loop
                    self._reset_drive_tracking()
                    self.state = State.SEARCH
                    return self.state, Command(0.0, 0.0)
                return self.state, Command(0.0, 0.0)

            # cluster is None while driving
            since_seen = 999.0
            if self.last_cluster_seen_s is not None:
                since_seen = wm.now_s - self.last_cluster_seen_s

            if since_seen <= params.DRIVE_LOST_AS_REACHED_TIMEOUT_S:
                # assume collected
                self._reset_drive_tracking()
                self.state = State.SEARCH
                return self.state, Command(0.0, 0.0)

            # otherwise stop and go search again
            self._reset_drive_tracking()
            self.state = State.SEARCH
            return self.state, Command(0.0, 0.0)

        # fallback
        self.state = State.SEARCH
        return self.state, Command(0.0, 0.0)

    def _reset_drive_tracking(self):
        self.drive_started_s = None
        self.last_cluster_seen_s = None
