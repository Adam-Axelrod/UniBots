"""
Compute x, y, heading from raw MPU6050 IMU data.
Heading from gyro integration; x,y from accelerometer integration in world frame.
"""
import math
from dataclasses import dataclass
from typing import Tuple


# MPU6050 scale factors
GYRO_SCALE = 131.0  # LSB per deg/s at ±250°/s
ACCEL_SCALE = 16384.0  # LSB per g at ±2g
G = 9.81


@dataclass
class PoseState:
    """State persisted across pose updates."""
    heading_rad: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    x: float = 0.0
    y: float = 0.0


def compute_pose_from_imu(
    gyro_z_raw: int,
    accel_x_raw: int,
    accel_y_raw: int,
    dt: float,
    state: PoseState,
) -> Tuple[float, float, float, PoseState]:
    """
    Compute x, y, heading from raw MPU6050 data.

    Args:
        gyro_z_raw: Raw 16-bit gyro Z value (LSB)
        accel_x_raw: Raw 16-bit accelerometer X value (LSB)
        accel_y_raw: Raw 16-bit accelerometer Y value (LSB)
        dt: Time step in seconds
        state: Previous pose state

    Returns:
        (x, y, heading_deg, updated_state)
        Coordinate convention: X forward, Y left, heading 0° = +X, increasing CCW (ROS)
    """
    # Gyro: convert to deg/s and integrate heading
    gyro_z_deg_s = gyro_z_raw / GYRO_SCALE
    heading_rad = state.heading_rad + math.radians(gyro_z_deg_s) * dt

    # Accel: convert raw to m/s² (body frame)
    ax_body = accel_x_raw / ACCEL_SCALE * G
    ay_body = accel_y_raw / ACCEL_SCALE * G

    # Rotate accel from body to world frame
    c = math.cos(heading_rad)
    s = math.sin(heading_rad)
    ax_world = ax_body * c - ay_body * s
    ay_world = ax_body * s + ay_body * c

    # Integrate velocity
    vx = state.vx + ax_world * dt
    vy = state.vy + ay_world * dt

    # Integrate position
    x = state.x + vx * dt
    y = state.y + vy * dt

    heading_deg = math.degrees(heading_rad)
    new_state = PoseState(
        heading_rad=heading_rad,
        vx=vx,
        vy=vy,
        x=x,
        y=y,
    )
    return x, y, heading_deg, new_state
