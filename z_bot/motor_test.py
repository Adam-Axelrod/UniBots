#!/usr/bin/env python3
import time
import lgpio

THROTTLE_GPIO = 18  # change if needed
STEER_GPIO    = 19  # change if needed

# Typical servo timing
FREQ_HZ = 50

def main():
    h = lgpio.gpiochip_open(0)

    # Start both channels at neutral 1500us
    lgpio.tx_servo(h, THROTTLE_GPIO, 1500, FREQ_HZ)
    lgpio.tx_servo(h, STEER_GPIO,    1500, FREQ_HZ)
    print("Neutral 1500us set. Plug in ESC battery now (if not already).")
    time.sleep(3)

    print("Slight forward (1600us) for 2s...")
    lgpio.tx_servo(h, THROTTLE_GPIO, 1600, FREQ_HZ)
    time.sleep(2)

    print("Back to neutral (1500us) for 2s...")
    lgpio.tx_servo(h, THROTTLE_GPIO, 1500, FREQ_HZ)
    time.sleep(2)

    print("Slight reverse (1400us) for 2s...")
    lgpio.tx_servo(h, THROTTLE_GPIO, 1400, FREQ_HZ)
    time.sleep(2)

    print("Neutral...")
    lgpio.tx_servo(h, THROTTLE_GPIO, 1500, FREQ_HZ)
    time.sleep(1)

    print("Steer right (1600us) for 1s...")
    lgpio.tx_servo(h, STEER_GPIO, 1600, FREQ_HZ)
    time.sleep(1)

    print("Steer left (1400us) for 1s...")
    lgpio.tx_servo(h, STEER_GPIO, 1400, FREQ_HZ)
    time.sleep(1)

    print("Neutral + stop pulses")
    lgpio.tx_servo(h, THROTTLE_GPIO, 0, FREQ_HZ)  # 0 disables servo pulses
    lgpio.tx_servo(h, STEER_GPIO,    0, FREQ_HZ)

    lgpio.gpiochip_close(h)

if __name__ == "__main__":
    main()
