import RPi.GPIO as GPIO
import time

BUZZER = 18

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER, GPIO.OUT)

pwm = GPIO.PWM(BUZZER, 1000)  # 1kHz
pwm.start(50)                 # 50% duty cycle

time.sleep(0.5)

pwm.stop()
GPIO.cleanup()
