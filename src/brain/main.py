"""
Brain entrypoint: wire sensors → Process → actuators + debug frame sink.
Run from repo root:  python src/brain/main.py
"""

import os
import sys

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from brain.config import Config, load_config  # noqa: E402
from brain.process import ProcessPipeline  # noqa: E402
from debugger import create_frame_sink  # noqa: E402
from input.camera import create_front_camera, create_rear_camera  # noqa: E402
from input.encoders import create_encoders  # noqa: E402
from input.imu import create_imu  # noqa: E402
from input.ultrasonic import create_ultrasonic  # noqa: E402
from output.motor_controller import create_motor_controller  # noqa: E402
from output.speaker import create_speaker  # noqa: E402


def run(cfg: Config) -> None:
    """Sensors init() → get_data() loop → ProcessPipeline → frame_sink.send(). Actuators ready for FSM."""
    camera_front = create_front_camera(cfg)
    camera_rear = create_rear_camera(cfg)
    ultrasonic = create_ultrasonic(cfg)
    encoders = create_encoders(cfg)
    imu = create_imu(cfg)

    motor = create_motor_controller(cfg)
    speaker = create_speaker(cfg)
    frame_sink = create_frame_sink(cfg)

    camera_front.init()
    camera_rear.init()
    ultrasonic.init()
    encoders.init()
    if imu:
        imu.init()
    motor.init()
    speaker.init()
    frame_sink.start()

    process = ProcessPipeline(cfg.MODEL_PATH, cfg.CONF_THRESHOLD)

    print("[Main] Loop: sensors → process → frame_sink (motor, speaker ready for FSM)")
    try:
        while True:
            front_frame = camera_front.get_data()
            rear_frame = camera_rear.get_data()
            distance = ultrasonic.get_data()
            left, right = encoders.get_data()
            heading = imu.get_data() if imu else None

            if front_frame is None:
                continue
            annotated = process(front_frame)
            if frame_sink.send(annotated):
                break
    finally:
        print("[Main] Cleanup")
        camera_front.stop()
        camera_rear.stop()
        ultrasonic.stop()
        encoders.stop()
        if imu:
            imu.stop()
        motor.stop()
        speaker.stop()
        frame_sink.close()


if __name__ == "__main__":
    run(load_config())
