# =========================
# Mission timing (optional for now)
# =========================
RUN_TIME_S = 180.0  # 3 minutes

# =========================
# Avoidance (highest priority)
# =========================
AVOID_DISTANCE_CM = 25.0
# TODO: future - hysteresis when re-entering after avoid
AVOID_CLEAR_HYST_CM = 7.0
# TODO: future - backup before turning when very close
AVOID_BACKUP_CM = 15.0
AVOID_BACKUP_SPEED = 0.5
# Avoid turn angular speed (positive = right)
AVOID_TURN_SPEED = 0.4
# Degrees to turn before exiting AVOID (90 = quarter turn)
AVOID_TURN_ANGLE_DEG = 90.0

# =========================
# Align / Drive
# =========================
# Threshold for "centered" (abs(side) < this = centered). Avoids float oscillation.
SIDE_EPSILON = 0.01

# TODO: future - stop when cluster centroid near bottom of frame
# For 240px height, 210-235 is typical.
DRIVE_STOP_CY_PX = 210.0

# TODO: future - if cluster disappears shortly after DRIVE, treat as "collected"
DRIVE_LOST_AS_REACHED_TIMEOUT_S = 0.8

# Grace period: if cluster lost briefly in DRIVE, wait before SEARCH (avoids drive/align/search oscillation)
DRIVE_LOST_GRACE_S = 0.5  # Used by FSM

# TODO: future - after leaving DRIVE, stay in SEARCH before allowing ALIGN
SEARCH_COOLDOWN_AFTER_DRIVE_S = 1.5

# If no cluster while aligning, go to SEARCH (spin)
SEARCH_WHEN_NO_CLUSTER = True

# Grace period: if cluster lost briefly in ALIGN, wait before SEARCH (avoids flicker/overshoot)
ALIGN_LOST_GRACE_S = 0.6  # Used by FSM

# TODO: future - align turn rate when wiring ALIGN_SPEED scaling
ALIGN_TURN_RATE = 0.25
# Drive forward speed when pursuing cluster
DRIVE_SPEED = 0.8
# Align angular speed when centering on cluster
ALIGN_SPEED = 2.0

# =========================
# Active SEARCH (lawn-mower)
# =========================
SEARCH_DRIVE_S = 2.0
SEARCH_TURN_S = 1.5
SEARCH_TURN_ANGLE_DEG = 360.0

# Chunked search turn: rotate CHUNK_DEG at speed, pause, repeat until 360
SEARCH_TURN_CHUNK_DEG = 15.0
SEARCH_TURN_SPEED = 0.3
SEARCH_TURN_PAUSE_S = 0.8
SEARCH_FORWARD_SPEED = 0.2

# =========================
# Go-Home (AprilTag-based)
# =========================
GO_HOME_TRIGGER_S = 30.0  # Start go-home this many seconds before RUN_TIME_S
NAV_CLOSE_CM = 30.0  # Switch from NAVIGATE to CENTER when this close to wall
PARK_CLOSE_CM = 10.0  # Switch to PARK_PARALLEL when this close
GO_HOME_NAV_SPEED = 0.5  # Forward speed during NAVIGATE
GO_HOME_TURN_SPEED = 0.3  # Turn speed when re-acquiring or turning to home
CENTER_EPSILON_PX = 20.0  # Consider centered when offset < this (image px)
PARALLEL_EPSILON_DEG = 5.0  # Consider parallel when angle error < this
