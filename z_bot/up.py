from gpiozero import Motor
from time import sleep

motorA = Motor(forward=19, backward=26)
motorB = Motor(forward=22, backward=23)

while True:
    motorA.forward()
    motorB.forward()
    sleep(2)
    motorA.backward()
    motorB.backward()
    sleep(2)
    motorA.stop()
    motorB.stop()
    sleep(1)
