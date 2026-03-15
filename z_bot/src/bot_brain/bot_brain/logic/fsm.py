from enum import Enum, auto
from typing import Optional, Tuple

from .world_model import WorldModel
from .command import Command
from . import params


class State(Enum):
    SEARCH = auto()
    ALIGN = auto()
    DRIVE = auto()
    AVOID = auto()
    GO_HOME = auto()


class BrainFSM:

    def __init__(self):

        self.state = State.SEARCH

        self.drive_started_s: Optional[float] = None
        self.last_cluster_seen_s: Optional[float] = None


    def update(self, wm: WorldModel) -> Tuple[State, Command]:

        # Track last time ball was seen
        if wm.cluster is not None:
            self.last_cluster_seen_s = wm.now_s


        # =================================
        # SEARCH
        # =================================
        if self.state == State.SEARCH:

            if wm.cluster is not None:
                self.state = State.ALIGN
                return self.state, Command(0.0, 0.0)

            return self.state, Command(0.0, 0.0)


        # =================================
        # ALIGN
        # =================================
        if self.state == State.ALIGN:

            if wm.cluster is None:
                self.state = State.SEARCH
                return self.state, Command(0.0, 0.0)

            side = wm.cluster.side

            # Ball centered
            if side == 0.0:
                self.state = State.DRIVE
                self.drive_started_s = wm.now_s
                return self.state, Command(0.0, 0.0)

            # Ball left → turn left
            if side < 0:
                return self.state, Command(0.0, 0.4)

            # Ball right → turn right
            if side > 0:
                return self.state, Command(0.0, -0.4)


        # =================================
        # DRIVE
        # =================================
        if self.state == State.DRIVE:

            if wm.cluster is not None:

                # Ball close enough
                if wm.cluster.cy >= params.DRIVE_STOP_CY_PX:
                    self.state = State.SEARCH
                    return self.state, Command(0.0, 0.0)

                # Drive forward
                return self.state, Command(1.0, 0.0)

            # Lost ball
            self.state = State.SEARCH
            return self.state, Command(0.0, 0.0)


        # Fallback
        self.state = State.SEARCH
        return self.state, Command(0.0, 0.0)
