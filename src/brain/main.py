"""
Brain entrypoint: inputs → WorldModel → FSM → Command → output.
Run from repo root:  python src/brain/main.py
"""

import os
import sys
import time

import cv2

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from brain.april import AprilTagDetector, get_home_center_tag_ids  # noqa: E402
from brain.config import Config, load_config  # noqa: E402
from brain.fsm import FSM, State  # noqa: E402
from brain.process import VisionModule, compute_path, format_cmd  # noqa: E402
from brain.wall_color import detect_wall_color  # noqa: E402
from brain.world_model import WorldModel  # noqa: E402
from debugger import create_frame_sink  # noqa: E402
from debugger.annotator import Annotator, DebugInfo  # noqa: E402
from input.camera import create_front_camera  # noqa: E402
from input.encoders import create_encoders  # noqa: E402
from input.imu import create_imu  # noqa: E402
from input.unity_sim_connection import UnitySimConnection  # noqa: E402
from input.ultrasonic import create_ultrasonic  # noqa: E402
from output.executor import Executor  # noqa: E402
from output.motor_controller import create_motor_controller  # noqa: E402
from output.speaker import create_speaker  # noqa: E402

OBSTACLE_THRESHOLD_CM = 30.0
HOME_THRESHOLD_CM = 40.0
WALL_CLOSE_CM = 50.0
HOME_TAG_AREA_MIN = 500.0  # min pixel area for "at home"
CENTER_MARGIN_PX = 80
ALIGN_CENTER_MARGIN_PX = 30  # tighter margin for drop alignment


def run(cfg: Config) -> None:
    """Inputs → WorldModel → FSM → Command → Executor."""
    unity_conn: UnitySimConnection | None = None
    if cfg.INPUT_MODE == "sim" or cfg.ACTUATOR_MODE == "sim":
        unity_conn = UnitySimConnection(cfg.UNITY_FRONT_HOST, cfg.UNITY_FRONT_PORT)
        unity_conn.init()

    camera_front = create_front_camera(
        cfg, unity_conn=unity_conn if cfg.INPUT_MODE == "sim" else None
    )
    ultrasonic = create_ultrasonic(
        cfg, unity_conn=unity_conn if cfg.INPUT_MODE == "sim" else None
    )
    encoders = create_encoders(cfg)
    imu = create_imu(cfg)

    motor = create_motor_controller(
        cfg, unity_conn=unity_conn if cfg.ACTUATOR_MODE == "sim" else None
    )
    speaker = create_speaker(cfg)
    executor = Executor(motor, speaker, drop_mechanism=None)
    frame_sink = create_frame_sink(cfg)

    frame_sink.start()

    camera_front.init()
    ultrasonic.init()
    encoders.init()
    if imu:
        imu.init()
    motor.init()
    speaker.init()

    vision = VisionModule(cfg.MODEL_PATH, cfg.CONF_THRESHOLD)
    april_detector = AprilTagDetector(cfg.HOME_ZONE)
    annotator = Annotator()
    fsm = FSM()
    if cfg.DEBUG_START_STATE:
        try:
            start_state = State[cfg.DEBUG_START_STATE]
        except KeyError:
            valid = ", ".join(s.name for s in State)
            raise ValueError(
                f"Invalid debug_start_state: {cfg.DEBUG_START_STATE!r}. Must be one of: {valid}"
            )
        fsm.state = start_state
        fsm._prev_state = None
        print(f"[Main] Debug: starting in state {fsm.state.name}")

    start_time = time.monotonic()
    prev_ball_detected = False
    fps = 0.0

    print("[Main] Loop: inputs → world_model → fsm → command → executor")
    try:
        while True:
            loop_start = time.monotonic()
            front_frame = camera_front.get_data()
            distance = ultrasonic.get_data()
            left, right = encoders.get_data()
            heading = imu.get_data() if imu else None

            if front_frame is None:
                continue

            raw_frame = front_frame
            if cfg.FRAME_WIDTH > 0 and cfg.FRAME_HEIGHT > 0:
                front_frame = cv2.resize(
                    raw_frame, (cfg.FRAME_WIDTH, cfg.FRAME_HEIGHT)
                )
            if cfg.APRIL_FRAME_WIDTH > 0 and cfg.APRIL_FRAME_HEIGHT > 0:
                april_frame = cv2.resize(
                    raw_frame,
                    (cfg.APRIL_FRAME_WIDTH, cfg.APRIL_FRAME_HEIGHT),
                )
            else:
                april_frame = front_frame

            ball_centers, annotated_base = vision.get_detections(front_frame)
            h, w = front_frame.shape[:2]
            camera_point = (w // 2, h)
            path = compute_path(ball_centers, camera_point)
            ball_detected = len(ball_centers) > 0
            target_ball = path[0] if path else None

            elapsed = time.monotonic() - start_time
            time_remaining = max(0.0, 60.0 - elapsed)
            time_low = time_remaining < 10.0

            distance_val = distance if distance is not None else 0.0
            obstacle = 0 < distance_val < OBSTACLE_THRESHOLD_CM
            obstacle_cleared = not obstacle

            # AprilTag homing (sim camera sends RGB); use april_frame if higher-res configured
            home_detections = april_detector.detect(
                april_frame, frame_rgb=(cfg.INPUT_MODE == "sim")
            )
            # Scale tag centers from april_frame to display (front_frame) coords for overlay
            ah, aw = april_frame.shape[:2]
            sx = w / aw if aw else 1.0
            sy = h / ah if ah else 1.0
            april_tags_display = [
                (int(d.center_x * sx), int(d.center_y * sy), d.tag_id)
                for d in home_detections
            ]
            home_tag_visible = len(home_detections) > 0
            home_tag_center = None
            home_tag_id = None
            home_tag_area = 0.0
            home_tag_centered = False
            home_tag_align_centered = False
            home_tag_left_of_center = False
            if home_detections:
                best = max(home_detections, key=lambda d: d.area)
                home_tag_center = (int(best.center_x), int(best.center_y))
                home_tag_id = best.tag_id
                home_tag_area = best.area
                frame_center_x = w // 2
                home_tag_centered = abs(best.center_x - frame_center_x) <= CENTER_MARGIN_PX
                home_tag_align_centered = (
                    abs(best.center_x - frame_center_x) <= ALIGN_CENTER_MARGIN_PX
                )
                home_tag_left_of_center = best.center_x < frame_center_x

            # Wall color (when close to wall). Sim camera returns RGB; convert to BGR for HSV.
            home_wall_visible = False
            if distance_val < WALL_CLOSE_CM:
                wall_frame = (
                    cv2.cvtColor(front_frame, cv2.COLOR_RGB2BGR)
                    if cfg.INPUT_MODE == "sim"
                    else front_frame
                )
                wall_result = detect_wall_color(wall_frame, cfg.HOME_ZONE)
                home_wall_visible = wall_result.matches_home

            at_home = (
                home_tag_visible
                and home_tag_area >= HOME_TAG_AREA_MIN
                and distance_val < HOME_THRESHOLD_CM
            )
            wall_visible = at_home
            center_lo, center_hi = get_home_center_tag_ids(cfg.HOME_ZONE)
            at_home_center = at_home and (
                home_tag_id is not None and home_tag_id in (center_lo, center_hi)
            )

            wm = WorldModel(
                ball_detected=ball_detected,
                target_ball=target_ball,
                ball_lost=prev_ball_detected and not ball_detected,
                obstacle=obstacle,
                obstacle_cleared=obstacle_cleared,
                time_low=time_low,
                wall_visible=wall_visible,
                start_signal=True,
                home_tag_visible=home_tag_visible,
                home_tag_center=home_tag_center,
                home_tag_id=home_tag_id,
                home_tag_area=home_tag_area,
                home_tag_centered=home_tag_centered,
                home_tag_align_centered=home_tag_align_centered,
                home_tag_left_of_center=home_tag_left_of_center,
                home_wall_visible=home_wall_visible,
                at_home=at_home,
                at_home_center=at_home_center,
                home_center_tag_lo=center_lo,
                home_center_tag_hi=center_hi,
            )
            prev_ball_detected = ball_detected

            state, cmd = fsm.update(wm)
            executor.execute(cmd)

            loop_time_ms = (time.monotonic() - loop_start) * 1000
            if loop_time_ms > 0:
                fps = 1000.0 / loop_time_ms
            home_tag_info = (
                f"Tags: {len(home_detections)}"
                + (f" id={home_tag_id}" if home_tag_id is not None else "")
            )
            debug = DebugInfo(
                state_name=state.name,
                cmd_str=format_cmd(cmd.motor, cmd.beep, cmd.drop),
                fps=fps,
                loop_time_ms=loop_time_ms,
                ball_count=len(ball_centers),
                time_remaining=time_remaining,
                home_tag_info=home_tag_info,
                april_tags=april_tags_display,
            )
            annotated = annotator(annotated_base, path, camera_point, debug)
            if frame_sink.send(annotated):
                break
    except Exception:
        raise
    finally:
        print("[Main] Cleanup")
        camera_front.stop()
        ultrasonic.stop()
        encoders.stop()
        if imu:
            imu.stop()
        motor.stop()
        speaker.stop()
        frame_sink.close()
        if unity_conn is not None:
            unity_conn.close()


if __name__ == "__main__":
    run(load_config())
