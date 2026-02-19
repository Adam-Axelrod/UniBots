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

from brain.config import Config, load_config  # noqa: E402
from brain.fsm import FSM  # noqa: E402
from brain.process import VisionModule, compute_path, format_cmd  # noqa: E402
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
    annotator = Annotator()
    fsm = FSM()

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

            if cfg.FRAME_WIDTH > 0 and cfg.FRAME_HEIGHT > 0:
                front_frame = cv2.resize(
                    front_frame, (cfg.FRAME_WIDTH, cfg.FRAME_HEIGHT)
                )

            ball_centers, annotated_base = vision.get_detections(front_frame)
            h, w = front_frame.shape[:2]
            camera_point = (w // 2, h)
            path = compute_path(ball_centers, camera_point)
            ball_detected = len(ball_centers) > 0
            target_ball = path[0] if path else None

            elapsed = time.monotonic() - start_time
            time_remaining = max(0.0, 120.0 - elapsed)
            time_low = time_remaining < 60.0

            distance_val = distance if distance is not None else 0.0
            obstacle = 0 < distance_val < OBSTACLE_THRESHOLD_CM
            obstacle_cleared = not obstacle

            wm = WorldModel(
                ball_detected=ball_detected,
                target_ball=target_ball,
                ball_lost=prev_ball_detected and not ball_detected,
                obstacle=obstacle,
                obstacle_cleared=obstacle_cleared,
                time_low=time_low,
                wall_visible=False,
                start_signal=True,
            )
            prev_ball_detected = ball_detected

            state, cmd = fsm.update(wm)
            executor.execute(cmd)

            loop_time_ms = (time.monotonic() - loop_start) * 1000
            if loop_time_ms > 0:
                fps = 1000.0 / loop_time_ms
            debug = DebugInfo(
                state_name=state.name,
                cmd_str=format_cmd(cmd.motor, cmd.beep, cmd.drop),
                fps=fps,
                loop_time_ms=loop_time_ms,
                ball_count=len(ball_centers),
                time_remaining=time_remaining,
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
