#!/usr/bin/env python3

from gpiozero import PWMOutputDevice, DigitalOutputDevice
from time import sleep

# ---------------- PIN SETUP ----------------

# Motor A (Left)
pwm_a = PWMOutputDevice(12)
ain1 = DigitalOutputDevice(17)
ain2 = DigitalOutputDevice(27)

# Motor B (Right)
pwm_b = PWMOutputDevice(13)
bin1 = DigitalOutputDevice(23)
bin2 = DigitalOutputDevice(24)

# Standby
stby = DigitalOutputDevice(22)

# ------------- SETTINGS --------------------

ROTATION_SPEED = 0.6     # 0.0 → 1.0
ROTATION_TIME  = 5.4    # seconds (tune this)

# -------------------------------------------


def motor_right(speed):
    """Spin robot right on the spot"""

    stby.on()

    # Left motor forward
    ain1.on()
    ain2.off()
    pwm_a.value = speed

    # Right motor backward
    bin1.off()
    bin2.on()
    pwm_b.value = speed

    print(f"Rotating RIGHT at {speed*100:.0f}% power")


def motor_stop():
    pwm_a.value = 0
    pwm_b.value = 0
    stby.off()
    print("Motors stopped")


def main():

    print("\n--- 360 Rotation Test ---")
    print(f"Speed: {ROTATION_SPEED}")
    print(f"Time : {ROTATION_TIME} seconds\n")

    sleep(2)

    try:
        motor_right(ROTATION_SPEED)
        sleep(ROTATION_TIME)
        motor_stop()

        print("\nRotation complete.")
        print("Adjust ROTATION_TIME until robot spins exactly 360 degrees.")

    except KeyboardInterrupt:
        motor_stop()
        print("\nTest cancelled")


if __name__ == "__main__":
    main()
