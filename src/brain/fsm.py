"""
FSM skeleton based on Design.md.

States and transitions mirror the spec. Handlers are stubbed for later implementation.
"""

from dataclasses import dataclass
from enum import Enum, auto


class State(Enum):
    INIT = auto()
    SEARCH_BALL = auto()
    DRIVE_TO_BALL = auto()
    GO_TO_WALL = auto()
    ALIGN_AND_DROP = auto()
    PARK = auto()
    AVOID_OBSTACLE = auto()


@dataclass
class Sensors:
    """Stub sensor bundle; real implementation will populate these fields."""

    start_signal: bool = False
    ball_detected: bool = False
    ball_collected: bool = False
    ball_lost: bool = False
    balls_full: bool = False
    time_low: bool = False
    wall_visible: bool = False
    obstacle: bool = False
    obstacle_cleared: bool = False


class FSM:
    """Finite-state machine skeleton (no hardware calls)."""

    def __init__(self):
        self.state = State.INIT
        self._prev_state: State | None = None

    def update(self, sensors: Sensors) -> State:
        # Interrupt-style obstacle handling
        if sensors.obstacle and self.state != State.AVOID_OBSTACLE:
            self._prev_state = self.state
            self.state = State.AVOID_OBSTACLE

        if self.state == State.INIT:
            self._init(sensors)
        elif self.state == State.SEARCH_BALL:
            self._search_ball(sensors)
        elif self.state == State.DRIVE_TO_BALL:
            self._drive_to_ball(sensors)
        elif self.state == State.GO_TO_WALL:
            self._go_to_wall(sensors)
        elif self.state == State.ALIGN_AND_DROP:
            self._align_and_drop(sensors)
        elif self.state == State.PARK:
            self._park(sensors)
        elif self.state == State.AVOID_OBSTACLE:
            self._avoid_obstacle(sensors)

        return self.state

    # ---- State handlers (stubs) ----

    def _init(self, sensors: Sensors) -> None:
        # TODO: wait for start; reset counters/timers; enable intake
        if sensors.start_signal:
            self.state = State.SEARCH_BALL

    def _search_ball(self, sensors: Sensors) -> None:
        # TODO: wander/sweep arena
        if sensors.ball_detected:
            self.state = State.DRIVE_TO_BALL
        elif sensors.balls_full or sensors.time_low:
            self.state = State.GO_TO_WALL

    def _drive_to_ball(self, sensors: Sensors) -> None:
        # TODO: face ball, drive forward, maintain heading
        if sensors.ball_collected or sensors.ball_lost:
            self.state = State.SEARCH_BALL
        elif sensors.balls_full:
            self.state = State.GO_TO_WALL

    def _go_to_wall(self, sensors: Sensors) -> None:
        # TODO: orient to wall, drive forward, avoid obstacles
        if sensors.wall_visible:
            self.state = State.ALIGN_AND_DROP

    def _align_and_drop(self, sensors: Sensors) -> None:
        # TODO: align parallel, drop balls
        self.state = State.PARK

    def _park(self, sensors: Sensors) -> None:
        # TODO: drive slowly until touching wall, stop forever
        pass

    def _avoid_obstacle(self, sensors: Sensors) -> None:
        # TODO: local turn + short move, resume prev state
        if sensors.obstacle_cleared:
            self.state = self._prev_state or State.SEARCH_BALL
