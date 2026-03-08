import os
import time

# PWM0 on the Pi 5 is typically export 0 or 2 depending on overlay
PWM_PATH = "/sys/class/pwm/pwmchip0/pwm0/"

def write_pwm(file, value):
    with open(os.path.join(PWM_PATH, file), 'w') as f:
        f.write(str(value))

# 1. Export the PWM pin (if not already exported)
# echo 0 > /sys/class/pwm/pwmchip0/export

# 2. Set Period (20ms for ESCs = 20,000,000 nanoseconds)
write_pwm("period", 20000000)

# 3. Set Duty Cycle (1.5ms Neutral = 1,500,000 nanoseconds)
write_pwm("duty_cycle", 15000000)

# 4. Enable
write_pwm("enable", 1)

time.sleep(5)

# 5. Disable
write_pwm("enable", 0)