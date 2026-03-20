"""
AprilTag detection for homing. Zone maps to tag ID range per Unibots rules.
"""

from dataclasses import dataclass

import cv2
import numpy as np
from pupil_apriltags import Detector

# Zone -> AprilTag ID range (inclusive) per Rules.md 4.5.4
ZONE_TAG_RANGES: dict[str, tuple[int, int]] = {
    "North": (0, 5),
    "East": (6, 11),
    "South": (12, 17),
    "West": (18, 23),
}


def get_home_center_tag_ids(home_zone: str) -> tuple[int, int]:
    """Return (center_lo, center_hi) tag IDs for the home zone (e.g. North -> 2, 3)."""
    r = ZONE_TAG_RANGES.get(home_zone, (0, 5))
    tag_min = r[0]
    return (tag_min + 2, tag_min + 3)


def wall_from_tag_id(tag_id: int) -> "str | None":
    """Return wall name for a tag ID, or None if invalid."""
    for wall, (lo, hi) in ZONE_TAG_RANGES.items():
        if lo <= tag_id <= hi:
            return wall
    return None


@dataclass
class AprilTagDetection:
    """Single AprilTag detection with corners for homography."""

    tag_id: int
    center_x: float
    center_y: float
    area: float
    corners: list[tuple[float, float]]  # 4 corners for homography


class AprilTagDetector:
    """Detects AprilTags (36h11). Filters to home_zone if set; else all tags (0-23)."""

    def __init__(self, home_zone: str | None = None):
        self._home_zone = home_zone
        if home_zone is None or home_zone == "all":
            self._tag_min, self._tag_max = 0, 23
        else:
            self._tag_min, self._tag_max = ZONE_TAG_RANGES.get(home_zone, (0, 5))
        self._detector = Detector(
            families="tag36h11",
            quad_decimate=1.0,
            quad_sigma=0.0,
            decode_sharpening=0.6,
        )

    def detect(
        self, frame: np.ndarray, *, frame_rgb: bool = False
    ) -> list[AprilTagDetection]:
        """Run detection on frame. Returns home-zone tags only."""
        if frame.ndim == 3:
            gray = cv2.cvtColor(
                frame,
                cv2.COLOR_RGB2GRAY if frame_rgb else cv2.COLOR_BGR2GRAY,
            )
        else:
            gray = frame

        gray = np.ascontiguousarray(gray)
        raw = self._detector.detect(gray)
        results: list[AprilTagDetection] = []

        for d in raw:
            if not (self._tag_min <= d.tag_id <= self._tag_max):
                continue
            cx, cy = d.center
            corners = [(float(c[0]), float(c[1])) for c in d.corners]
            xs = [c[0] for c in corners]
            ys = [c[1] for c in corners]
            area = (max(xs) - min(xs)) * (max(ys) - min(ys))
            results.append(
                AprilTagDetection(
                    tag_id=d.tag_id,
                    center_x=float(cx),
                    center_y=float(cy),
                    area=area,
                    corners=corners,
                )
            )

        return results
