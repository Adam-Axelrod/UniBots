"""
AprilTag detection for homing. Zone maps to tag ID range per Unibots rules.

Ideal for arena (far / rotated tags): full-res quad search (quad_decimate=1),
higher decode_sharpening for small tags, slight quad_sigma for noisy frames.
Run detection on as high a resolution as feasible (see config april_frame_*).
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


@dataclass
class AprilTagDetection:
    """Single AprilTag detection."""

    tag_id: int
    center_x: float
    center_y: float
    area: float


class AprilTagDetector:
    """Detects AprilTags (36h11) and filters to home-zone tags."""

    def __init__(self, home_zone: str):
        self._home_zone = home_zone
        self._tag_min, self._tag_max = ZONE_TAG_RANGES.get(
            home_zone, (0, 5)
        )
        # quad_decimate=1: full res for quad search (distant/small tags).
        # decode_sharpening: higher helps decode small tags (default 0.25).
        # quad_sigma=0: no blur (helps keep small-tag edges sharp).
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
            corners = d.corners
            xs = [c[0] for c in corners]
            ys = [c[1] for c in corners]
            area = (max(xs) - min(xs)) * (max(ys) - min(ys))
            results.append(
                AprilTagDetection(
                    tag_id=d.tag_id,
                    center_x=float(cx),
                    center_y=float(cy),
                    area=area,
                )
            )

        return results
