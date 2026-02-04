import pigpio

# Initialize the pigpio library
pi = pigpio.pi()

# Define servo GPIO pins
servo1_pin = 17
servo2_pin = 27

# Send neutral pulse (1500 microseconds) to both servos
pi.set_servo_pulsewidth(servo1_pin, 1500)
pi.set_servo_pulsewidth(servo2_pin, 1500)

# Clean up when done
pi.stop()