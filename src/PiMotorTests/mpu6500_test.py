#!/usr/bin/env python3
"""
MPU-6500 IMU test for Raspberry Pi.

Verifies I2C connection, wakes the device, and streams accelerometer,
gyroscope, and temperature readings.

Prerequisites:
  - Enable I2C: sudo raspi-config → Interface Options → I2C
  - Wiring: VCC→3.3V, GND→GND, SDA→GPIO 2 (pin 3), SCL→GPIO 3 (pin 5)
  - Verify device: i2cdetect -y 1  (should show 0x68 or 0x69)
"""

import struct
import sys
import time

try:
    from smbus2 import SMBus
except ImportError:
    print("Install smbus2: pip install smbus2")
    sys.exit(1)

# MPU-6500 registers
PWR_MGMT_1 = 0x6B
WHO_AM_I = 0x75
ACCEL_XOUT_H = 0x3B  # accel(6) + temp(2) + gyro(6) = 14 bytes

# Scale factors: 2g accel (16384 LSB/g), 250 deg/s gyro (131 LSB/(deg/s))
ACCEL_SO = 16384.0
GYRO_SO = 131.0
TEMP_SO = 333.87
TEMP_OFFSET = 21.0

I2C_BUS = 1
I2C_ADDR = 0x68  # 0x69 if AD0 pin is HIGH


def read_block(bus: SMBus, reg: int, length: int) -> bytes:
    """Read a block of bytes from a register."""
    return bytes(bus.read_i2c_block_data(I2C_ADDR, reg, length))


def write_byte(bus: SMBus, reg: int, value: int) -> None:
    """Write a byte to a register."""
    bus.write_byte_data(I2C_ADDR, reg, value)


def main() -> None:
    print("MPU-6500 Test - Ctrl+C to exit")

    with SMBus(I2C_BUS) as bus:
        # Wake from sleep (default after reset is sleep)
        write_byte(bus, PWR_MGMT_1, 0x00)
        time.sleep(0.1)

        # Verify device (0x70=MPU-6500, 0x71=MPU6250 SIP, 0x68=MPU-6050)
        whoami = bus.read_byte_data(I2C_ADDR, WHO_AM_I)
        if whoami not in (0x70, 0x71, 0x68):
            print(f"ERROR: WHO_AM_I=0x{whoami:02x} (expected 0x70, 0x71, or 0x68)")
            print("Check wiring and I2C address. Run: i2cdetect -y 1")
            sys.exit(1)
        chip = "MPU-6500" if whoami in (0x70, 0x71) else "MPU-6050"
        print(f"WHO_AM_I: 0x{whoami:02x} ({chip} detected)")
        print("---")

        try:
            while True:
                # Read 14 bytes: accel(6) + temp(2) + gyro(6) starting at 0x3B
                data = read_block(bus, ACCEL_XOUT_H, 14)
                if len(data) != 14:
                    print("Read error")
                    continue

                # Big-endian signed 16-bit
                ax, ay, az = struct.unpack(">hhh", data[0:6])
                temp_raw = struct.unpack(">h", data[6:8])[0]
                gx, gy, gz = struct.unpack(">hhh", data[8:14])

                accel_g = (ax / ACCEL_SO, ay / ACCEL_SO, az / ACCEL_SO)
                gyro_dps = (gx / GYRO_SO, gy / GYRO_SO, gz / GYRO_SO)
                temp_c = ((temp_raw - TEMP_OFFSET) / TEMP_SO) + TEMP_OFFSET

                print(
                    f"Accel (g): X={accel_g[0]:6.2f} Y={accel_g[1]:6.2f} Z={accel_g[2]:6.2f}  |  "
                    f"Gyro (deg/s): X={gyro_dps[0]:6.2f} Y={gyro_dps[1]:6.2f} Z={gyro_dps[2]:6.2f}  |  "
                    f"Temp: {temp_c:5.1f} C"
                )
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
