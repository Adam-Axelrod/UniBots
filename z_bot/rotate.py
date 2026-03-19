#!/usr/bin/env python3

import smbus2
import time
from gpiozero import PWMOutputDevice, DigitalOutputDevice


# =============================
# MPU6050 SETUP
# =============================

MPU6050_ADDR = 0x68
PWR_MGMT_1 = 0x6B
GYRO_XOUT = 0x43

bus = smbus2.SMBus(1)

# Wake up MPU6050
bus.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0)


def read_word(reg):

    high = bus.read_byte_data(MPU6050_ADDR, reg)
    low = bus.read_byte_data(MPU6050_ADDR, reg + 1)

    value = (high << 8) + low

    if value > 32768:
        value -= 65536

    return value


# =============================
# MOTOR SETUP
# =============================

# Motor A (left)
pwm_a = PWMOutputDevice(12)
ain1 = DigitalOutputDevice(17)
ain2 = DigitalOutputDevice(27)

# Motor B (right)
pwm_b = PWMOutputDevice(13)
bin1 = DigitalOutputDevice(23)
bin2 = DigitalOutputDevice(24)

# Standby pin
stby = DigitalOutputDevice(22)
stby.on()


# =============================
# MOTOR FUNCTIONS
# =============================

def motor_forward(speed):

    ain1.on()
    ain2.off()
    pwm_a.value = speed

    bin1.on()
    bin2.off()
    pwm_b.value = speed


def motor_backward(speed):

    ain1.off()
    ain2.on()
    pwm_a.value = speed

    bin1.off()
    bin2.on()
    pwm_b.value = speed


def motor_left(speed):

    # left wheel backward
    ain1.off()
    ain2.on()
    pwm_a.value = speed

    # right wheel forward
    bin1.on()
    bin2.off()
    pwm_b.value = speed


def motor_right(speed):

    # left wheel forward
    ain1.on()
    ain2.off()
    pwm_a.value = speed

    # right wheel backward
    bin1.off()
    bin2.on()
    pwm_b.value = speed


def motor_stop():

    pwm_a.value = 0
    pwm_b.value = 0


# =============================
# GYRO CALIBRATION
# =============================

print("Calibrating gyro... keep robot still")

bias = 0
samples = 200

for _ in range(samples):

    bias += read_word(GYRO_XOUT + 4)
    time.sleep(0.005)

bias /= samples

print("Gyro bias:", bias)


# =============================
# ROTATION (LEFT 90°)
# =============================

rotation = 0.0
last_time = time.time()

print("Starting 360° LEFT turn")

motor_forward(0.5)   # more stable speed
rotate_angle = 70

while True:

    gyro_raw = read_word(GYRO_XOUT + 4) - bias
    gyro_deg_s = gyro_raw / 131.0

    if abs(gyro_deg_s) < 0.5:
        gyro_deg_s = 0

    now = time.time()
    dt = now - last_time
    last_time = now

    rotation += gyro_deg_s * dt

    print(f"Rotation: {rotation:.2f}°")

    if rotation >= rotate_angle or rotation <= -rotate_angle:

        print("360° reached — stopping motors")
        motor_stop()
        break

    time.sleep(0.01)
