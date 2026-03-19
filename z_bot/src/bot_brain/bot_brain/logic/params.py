# =========================
# Mission timing (optional for now)
# =========================
RUN_TIME_S = 180.0  # 3 minutes

# =========================
# Avoidance (highest priority)
# =========================
AVOID_DISTANCE_CM = 25.0
AVOID_CLEAR_HYST_CM = 7.0

# For now: avoidance action is "turn right"
AVOID_TURN_RIGHT = True

# When very close, backup before turning (cm). 0 = disabled.
AVOID_BACKUP_CM = 15.0
AVOID_BACKUP_SPEED = 0.5

# =========================
# Align / Drive
# =========================
# Stop condition: cluster centroid goes near bottom of frame (ball pile under bot)
# For 240px height, 210-235 is typical.
DRIVE_STOP_CY_PX = 210.0

# If cluster disappears shortly after being seen during DRIVE, treat as "collected"
DRIVE_LOST_AS_REACHED_TIMEOUT_S = 0.8

# Grace period: if cluster lost briefly in DRIVE, wait before SEARCH (avoids drive/align/search oscillation)
DRIVE_LOST_GRACE_S = 0.5

# After leaving DRIVE, stay in SEARCH for this long before allowing ALIGN (breaks drive/align/search oscillation)
SEARCH_COOLDOWN_AFTER_DRIVE_S = 1.5

# If no cluster while aligning, go to SEARCH (spin)
SEARCH_WHEN_NO_CLUSTER = True

# Grace period: if cluster lost briefly in ALIGN, wait before SEARCH (avoids flicker/overshoot)
ALIGN_LOST_GRACE_S = 0.6

# Align turn rate (rad/s). Lower = less overshoot when centering.
ALIGN_TURN_RATE = 0.25

# =========================
# Active SEARCH (lawn-mower)
# =========================
SEARCH_DRIVE_S = 2.0
SEARCH_TURN_S = 1.5
SEARCH_TURN_ANGLE_DEG = 360.0
