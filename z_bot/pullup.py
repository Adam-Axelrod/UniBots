import RPi.GPIO as GPIO
import time

# Motor A pins
IN1 = 19  # GPIO17
IN2 = 26  # GPIO18


# DRV8833 STBY pin
STBY = 6  # GPIO24

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(STBY, GPIO.OUT)

# Start STBY high to enable motor driver
GPIO.output(STBY, GPIO.HIGH)

# PWM setup for speed control (1 kHz)
pwmA1 = GPIO.PWM(IN1, 1000)
pwmA2 = GPIO.PWM(IN2, 1000)

pwmA1.start(0)
pwmA2.start(0)

# Motor control functions
def motorA_forward(speed=100):
    pwmA1.ChangeDutyCycle(speed)
    pwmA2.ChangeDutyCycle(0)

def motorA_backward(speed=100):
    pwmA1.ChangeDutyCycle(0)
    pwmA2.ChangeDutyCycle(speed)

def stop_motors():
    pwmA1.ChangeDutyCycle(0)
    pwmA2.ChangeDutyCycle(0)
    pwmB1.ChangeDutyCycle(0)
    pwmB2.ChangeDutyCycle(0)

def standby(enable=True):
    GPIO.output(STBY, GPIO.HIGH if enable else GPIO.LOW)

# Main loop
try:
    while True:
        # Motors forward at 80% speed
        motorA_forward(80)
        time.sleep(2)
        
        # Motors backward at 60% speed
        motorA_backward(60)
        time.sleep(2)
        
        # Stop motors
        stop_motors()
        time.sleep(1)
        
        # Optional: put driver in standby for 1 second
        standby(False)
        print("Driver in standby")
        time.sleep(1)
        standby(True)
        print("Driver active")

except KeyboardInterrupt:
    stop_motors()
    GPIO.cleanup()
