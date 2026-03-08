from gpiozero import PWMOutputDevice, DigitalOutputDevice
from time import sleep

# --- Pin Setup ---
# PWM pin for speed control (0.0 to 1.0)
pwm_a = PWMOutputDevice(12) 
# Direction control pins
ain1 = DigitalOutputDevice(17)
ain2 = DigitalOutputDevice(27)
# Standby pin (Must be HIGH for the driver to work)
stby = DigitalOutputDevice(22)

def motor_forward(speed):
    stby.on()
    ain1.on()
    ain2.off()
    pwm_a.value = speed
    print(f"Moving Forward at {speed*100}% speed")

def motor_backward(speed):
    stby.on()
    ain1.off()
    ain2.on()
    pwm_a.value = speed
    print(f"Moving Backward at {speed*100}% speed")

def motor_stop():
    pwm_a.value = 0
    stby.off()
    print("Motor Stopped")

try:
    while True:
        # Move forward at half speed
        motor_forward(0.5)
        sleep(2)
        
        # Move forward at full speed
        motor_forward(1.0)
        sleep(2)
        
        # Stop
        motor_stop()
        sleep(1)
        
        # Move backward
        motor_backward(0.6)
        sleep(2)
        
        motor_stop()
        sleep(1)

except KeyboardInterrupt:
    # Graceful exit on Ctrl+C
    motor_stop()
    print("Script ended by user")