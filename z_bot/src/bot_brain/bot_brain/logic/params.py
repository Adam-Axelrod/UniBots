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

# =========================
# Align / Drive
# =========================
# Stop condition: cluster centroid goes near bottom of frame (ball pile under bot)
# For 240px height, 210-235 is typical.
DRIVE_STOP_CY_PX = 210.0

# If cluster disappears shortly after being seen during DRIVE, treat as "collected"
DRIVE_LOST_AS_REACHED_TIMEOUT_S = 0.8

# If no cluster while aligning, go to SEARCH (spin)
SEARCH_WHEN_NO_CLUSTER = True
