from gpiozero import Motor, PWMOutputDevice
from time import sleep

# Class for controlling a two-motor vehicle with an ESC
class VehicleESC:
    def __init__(self):
        # Initialize motors with PWM on appropriate GPIO pins
        self.left_motor = Motor(forward=17, backward=22)
        self.left_pwm = PWMOutputDevice(17)  # GPIO 17 controls the left motor
        self.right_motor = Motor(forward=22, backward=17)
        self.right_pwm = PWMOutputDevice(22)  # GPIO 22 controls the right motor

    # Method to set the speed of the left and right motors
    def set_speed(self, left_speed, right_speed):
        # Ensure speed values are in the range [0, 1]
        left_speed = max(0, min(1, left_speed))
        right_speed = max(0, min(1, right_speed))

        # Set PWM values for the motors
        self.left_pwm.value = left_speed
        self.right_pwm.value = right_speed

    # Stop both motors
    def stop(self):
        self.left_motor.stop()
        self.right_motor.stop()

# Create an instance of VehicleESC
rpi_vehicle = VehicleESC()

# Set left motor to 50% speed and right motor to 10% speed
try:
    print("Setting left motor speed to 50% and right motor speed to 10%.")
    rpi_vehicle.set_speed(left_speed=0.5, right_speed=0.1)
    sleep(10)  # Keep motors running for 10 seconds as a demonstration
except KeyboardInterrupt:
    print("Interrupted! Stopping motors.")
finally:
    print("Stopping motors.")
    rpi_vehicle.stop()