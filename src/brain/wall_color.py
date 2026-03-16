"""
Wall color detection for home validation. Compares dominant frame color to zone.
"""

from dataclasses import dataclass

import cv2
import numpy as np

# Zone -> (lower HSV, upper HSV) for OpenCV (H: 0-180, S: 0-255, V: 0-255)
ZONE_HSV_RANGES: dict[str, tuple[tuple[int, int, int], tuple[int, int, int]]] = {
    "Yellow": ((20, 100, 100), (30, 255, 255)),
    "Orange": ((10, 100, 100), (25, 255, 255)),
    "Purple": ((125, 80, 80), (155, 255, 255)),
    "Green": ((36, 100, 100), (70, 255, 255)),
}

# Zone -> wall color name per Rules.md
ZONE_WALL_COLOR: dict[str, str] = {
    "North": "Yellow",
    "East": "Orange",
    "South": "Purple",
    "West": "Green",
}


@dataclass
class WallColorResult:
    """Result of wall color check."""

    matches_home: bool
    dominant_hue: float | None


def detect_wall_color(
    frame: np.ndarray,
    home_zone: str,
    sample_frac: float = 0.3,
) -> WallColorResult:
    """
    Sample lower-center region of frame and check if dominant color matches home zone.

    Call when ultrasonic indicates close to wall. Returns matches_home=True if
    the dominant color falls within the home zone's HSV range.
    """
    if frame is None or frame.size == 0:
        return WallColorResult(matches_home=False, dominant_hue=None)

    h, w = frame.shape[:2]
    # Lower-center region (wall typically in lower part when camera faces forward)
    y_start = int(h * (1 - sample_frac))
    roi = frame[y_start:h, w // 4 : 3 * w // 4]

    if roi.size == 0:
        return WallColorResult(matches_home=False, dominant_hue=None)

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    # Use median to reduce noise from balls, shadows
    median_h = int(np.median(hsv[:, :, 0]))
    median_s = int(np.median(hsv[:, :, 1]))
    median_v = int(np.median(hsv[:, :, 2]))

    color_name = ZONE_WALL_COLOR.get(home_zone, "Yellow")
    lower, upper = ZONE_HSV_RANGES.get(
        color_name, ((20, 100, 100), (30, 255, 255))
    )

    in_range = (
        lower[0] <= median_h <= upper[0]
        and lower[1] <= median_s <= upper[1]
        and lower[2] <= median_v <= upper[2]
    )

    return WallColorResult(
        matches_home=in_range,
        dominant_hue=float(median_h) if in_range else None,
    )
