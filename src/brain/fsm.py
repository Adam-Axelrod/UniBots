"""
FSM: receives WorldModel, produces (State, Command).
"""

from enum import Enum, auto

from brain.command import Command, MotorDirection
from brain.world_model import WorldModel


class State(Enum):
    INIT = auto()
    SEARCH_BALL = auto()
    DRIVE_TO_BALL = auto()
    GO_TO_WALL = auto()
    ALIGN_AND_DROP = auto()
    PARK = auto()
    AVOID_OBSTACLE = auto()


class FSM:
    """Finite-state machine. update(WorldModel) -> (State, Command)."""

    def __init__(self):
        self.state = State.INIT
        self._prev_state: State | None = None

    def update(self, wm: WorldModel) -> tuple[State, Command]:
        cmd = Command()

        # Interrupt-style obstacle handling
        if wm.obstacle and self.state != State.AVOID_OBSTACLE:
            self._prev_state = self.state
            self.state = State.AVOID_OBSTACLE

        if self.state == State.INIT:
            cmd = self._init(wm)
        elif self.state == State.SEARCH_BALL:
            cmd = self._search_ball(wm)
        elif self.state == State.DRIVE_TO_BALL:
            cmd = self._drive_to_ball(wm)
        elif self.state == State.GO_TO_WALL:
            cmd = self._go_to_wall(wm)
        elif self.state == State.ALIGN_AND_DROP:
            cmd = self._align_and_drop(wm)
        elif self.state == State.PARK:
            cmd = self._park(wm)
        elif self.state == State.AVOID_OBSTACLE:
            cmd = self._avoid_obstacle(wm)

        return self.state, cmd

    def _init(self, wm: WorldModel) -> Command:
        if wm.start_signal:
            self.state = State.SEARCH_BALL
        return Command()

    def _search_ball(self, wm: WorldModel) -> Command:
        if wm.ball_detected:
            self.state = State.DRIVE_TO_BALL
        elif wm.time_low:
            self.state = State.GO_TO_WALL
        # Wander: slow rotation
        return Command(motor=MotorDirection.LEFT)

    def _drive_to_ball(self, wm: WorldModel) -> Command:
        if wm.ball_lost:
            self.state = State.SEARCH_BALL
        elif wm.time_low:
            self.state = State.GO_TO_WALL
        # Drive toward target_ball
        if wm.target_ball:
            return Command(motor=MotorDirection.FORWARD)
        return Command()

    def _go_to_wall(self, wm: WorldModel) -> Command:
        if wm.wall_visible:
            self.state = State.ALIGN_AND_DROP
        return Command(motor=MotorDirection.FORWARD)

    def _align_and_drop(self, wm: WorldModel) -> Command:
        self.state = State.PARK
        return Command(drop=True)

    def _park(self, wm: WorldModel) -> Command:
        return Command(motor=MotorDirection.FORWARD)

    def _avoid_obstacle(self, wm: WorldModel) -> Command:
        if wm.obstacle_cleared:
            self.state = self._prev_state or State.SEARCH_BALL
        return Command(motor=MotorDirection.LEFT)
