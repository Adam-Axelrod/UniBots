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
    GO_TO_HOME = auto()
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

        # Interrupt-style obstacle handling (disabled in PARK terminal state)
        if wm.obstacle and self.state != State.AVOID_OBSTACLE and self.state != State.PARK:
            self._prev_state = self.state
            self.state = State.AVOID_OBSTACLE

        if self.state == State.INIT:
            cmd = self._init(wm)
        elif self.state == State.SEARCH_BALL:
            cmd = self._search_ball(wm)
        elif self.state == State.DRIVE_TO_BALL:
            cmd = self._drive_to_ball(wm)
        elif self.state == State.GO_TO_HOME:
            cmd = self._go_to_home(wm)
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
            self.state = State.GO_TO_HOME
        # Wander: slow rotation
        return Command(motor=MotorDirection.LEFT)

    def _drive_to_ball(self, wm: WorldModel) -> Command:
        if wm.ball_lost:
            self.state = State.SEARCH_BALL
        elif wm.time_low:
            self.state = State.GO_TO_HOME
        elif not wm.target_ball:
            # No ball in view (e.g. returned from AVOID after losing sight)
            self.state = State.SEARCH_BALL
        # Drive toward target_ball
        if wm.target_ball:
            return Command(motor=MotorDirection.FORWARD)
        return Command()

    def _go_to_home(self, wm: WorldModel) -> Command:
        # Only transition when at center of home wall AND facing the wall (tag centered)
        if wm.at_home_center and wm.home_tag_centered:
            self.state = State.ALIGN_AND_DROP
            return Command()
        # At center but not facing wall: turn to center the tag (face dead on)
        if wm.at_home_center and wm.home_tag_visible and not wm.home_tag_centered:
            return Command(
                motor=MotorDirection.LEFT
                if wm.home_tag_left_of_center
                else MotorDirection.RIGHT
            )
        # At home but not at center: move along wall toward center (turn to slide, then forward)
        if wm.at_home and not wm.at_home_center:
            lo, hi = wm.home_center_tag_lo, wm.home_center_tag_hi
            if (
                wm.home_tag_id is not None
                and lo is not None
                and hi is not None
            ):
                if wm.home_tag_id < lo:
                    return Command(motor=MotorDirection.RIGHT)
                if wm.home_tag_id > hi:
                    return Command(motor=MotorDirection.LEFT)
        if wm.home_tag_visible:
            if not wm.home_tag_centered:
                return Command(
                    motor=MotorDirection.LEFT
                    if wm.home_tag_left_of_center
                    else MotorDirection.RIGHT
                )
            return Command(motor=MotorDirection.FORWARD)
        # No home tag visible: rotate to search
        return Command(motor=MotorDirection.LEFT)

    def _align_and_drop(self, wm: WorldModel) -> Command:
        if wm.home_tag_align_centered:
            self.state = State.PARK
            return Command(drop=True)
        # Micro-adjust to center tag before drop
        if wm.home_tag_visible and not wm.home_tag_align_centered:
            return Command(
                motor=MotorDirection.LEFT
                if wm.home_tag_left_of_center
                else MotorDirection.RIGHT
            )
        # No tag visible; drop anyway (fallback)
        self.state = State.PARK
        return Command(drop=True)

    def _park(self, wm: WorldModel) -> Command:
        return Command(motor=MotorDirection.STOP)

    def _avoid_obstacle(self, wm: WorldModel) -> Command:
        if wm.obstacle_cleared:
            self.state = self._prev_state or State.SEARCH_BALL
        return Command(motor=MotorDirection.LEFT)
