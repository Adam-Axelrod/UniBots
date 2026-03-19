from gpiozero import Motor, OutputDevice
from time import sleep

# --- Configuration ---
# Define GPIO pins (BCM numbering)
AIN1_PIN = 19  # Updated to your new pin
AIN2_PIN = 26  # Updated to your new pin
BIN1_PIN = 22  # Assuming this stays the same
BIN2_PIN = 23  # Assuming this stays the same
STBY_PIN = 6   # Updated to your new pin

# --- Initialization ---
# The DRV8833 requires the standby pin to be HIGH to operate
standby = OutputDevice(STBY_PIN)
standby.on()

# Initialize the motors using gpiozero's Motor class
# The Motor class takes (forward_pin, backward_pin)
motor_a = Motor(forward=AIN1_PIN, backward=AIN2_PIN)
motor_b = Motor(forward=BIN1_PIN, backward=BIN2_PIN)

# --- Execution ---
try:
    print("Motors going FORWARD at full speed...")
    # .forward(1.0) sets the speed to 100%
    motor_a.forward(1.0) 
    motor_b.forward(1.0)
    sleep(10) # Run for 3 seconds

except KeyboardInterrupt:
    print("\nProgram interrupted by user.")

finally:
    # Cleanup block ensures motors stop safely even if the script crashes
    print("Stopping motors and putting driver to sleep...")
    motor_a.stop()
    motor_b.stop()
    standby.off() # Pulling STBY low puts the DRV8833 into sleep mode to save power
