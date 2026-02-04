from gpiozero import PWMOutputDevice
from time import sleep

# Class for controlling two-motor vehicle (via PWM signals to ESCs)
class VehicleESC:
    def __init__(self):
        # Left motor connected to GPIO 17 (PWM signal to ESC controlling left motor)
        self.left_pwm = PWMOutputDevice(17)
        # Right motor connected to GPIO 22 (PWM signal to ESC controlling right motor)
        self.right_pwm = PWMOutputDevice(22)

    # Function for setting motor speeds
    def set_speed(self, left_speed, right_speed):
        # Ensure speed values are within range [0.0, 1.0] (percentage of full speed)
        left_speed = max(0.0, min(1.0, left_speed))
        right_speed = max(0.0, min(1.0, right_speed))

        # Set PWM values for both motors
        self.left_pwm.value = left_speed
        self.right_pwm.value = right_speed
        print(f"Left motor set to {left_speed * 100}%, Right motor set to {right_speed * 100}%")

    # Function to stop both motors
    def stop(self):
        self.left_pwm.value = 0
        self.right_pwm.value = 0
        print("Motors stopped.")

# Instantiate the vehicle
rpi_vehicle = VehicleESC()

# Main runtime to configure the motors
try:
    print("Starting motors...")
    # Set left motor to 50% and right motor to 10% speed
    rpi_vehicle.set_speed(left_speed=0.5, right_speed=0.1)

    # Keep running for 10 seconds
    sleep(10)

except KeyboardInterrupt:
    print("\nInterrupted! Stopping motors...")

finally:
    # Stop motors on exit
    rpi_vehicle.stop()