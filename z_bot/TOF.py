import time
import board
import busio
import adafruit_vl53l0x

i2c = busio.I2C(board.SCL, board.SDA)
tof = adafruit_vl53l0x.VL53L0X(i2c)

print("Filtered TOF Test")

history = []
WINDOW_SIZE = 5

while True:
    dist = tof.range

    history.append(dist)
    if len(history) > WINDOW_SIZE:
        history.pop(0)

    avg_dist = sum(history) / len(history)

    print(f"Raw: {dist} mm | Filtered: {int(avg_dist)} mm")

    time.sleep(0.1)
