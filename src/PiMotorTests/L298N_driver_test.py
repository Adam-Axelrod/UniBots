from gpiozero import Motor
from time import sleep

# Define the pins for Motor A
# forward=IN1, backward=IN2, enable=ENA
motor_a = Motor(forward=17, backward=27, enable=12)

def drive_sequence():
    try:
        print("Moving Forward at full speed...")
        motor_a.forward(speed=1.0)
        sleep(2)

        print("Moving Backward at half speed...")
        motor_a.backward(speed=0.5)
        sleep(2)

        print("Rotating slowly...")
        motor_a.forward(speed=0.3)
        sleep(2)

        print("Stopping...")
        motor_a.stop()
        sleep(1)

    except KeyboardInterrupt:
        motor_a.stop()
        print("\nScript stopped by user")

if __name__ == "__main__":
    drive_sequence()