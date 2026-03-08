from gpiozero import Servo
from time import sleep

# Raspberry Pi uses GPIO numbering (BCM), not physical pin numbers
# GPIO 5 and GPIO 10 correspond to specific pins on the header
motor_pin_1 = 19 # yellow 18
motor_pin_2 = 18 # white 19

# In gpiozero, Servo uses a range of -1 to 1. 
# 0 corresponds to the 'middle' or 1500 microseconds.
motor_turn = Servo(motor_pin_1)
motor_move = Servo(motor_pin_2)

def setup():
    print("Initializing motors...")
    # Setting to 0 is equivalent to writeMicroseconds(1500)
    motor_turn.value = 0
    motor_move.value = 0
    
    # Wait 2 seconds for the driver to initialize (same as your delay)
    sleep(2)
    print("Motors Ready!")

def loop():
    while True:
        # Example: To move motors like servo1.writeMicroseconds(2000)
        # Use motor_turn.value = 1.0
        # To move like servo1.writeMicroseconds(1000)
        motor_turn.value = 1.0
        motor_move.value = 0.0
        
        # Keep the script running
        sleep(1)

if __name__ == "__main__":
    try:
        setup()
        loop()
    except KeyboardInterrupt:
        # Cleanly stop if you press Ctrl+C
        motor_turn.value = None
        motor_move.value = None
        print("\nProgram stopped.")