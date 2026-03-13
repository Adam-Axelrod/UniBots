"""
Debug overlay: draws path, markers, and debug info on frames.
"""

from dataclasses import dataclass, field

import cv2
import numpy as np

REF_SIZE = 256  # reference frame size for overlay scaling


@dataclass
class DebugInfo:
    """Debug overlay data. Cheap to construct, no heavy compute."""

    state_name: str
    cmd_str: str
    fps: float
    loop_time_ms: float
    ball_count: int = 0
    time_remaining: float = 0.0
    home_tag_info: str = ""
    april_tags: list[tuple[int, int, int]] = field(default_factory=list)  # (x, y, tag_id) in display-frame coords


class Annotator:
    """Draws path, markers, and debug overlay on frame."""

    def __call__(
        self,
        frame: np.ndarray,
        path: list[tuple[int, int]],
        camera_point: tuple[int, int],
        debug: DebugInfo,
    ) -> np.ndarray:
        """Draw path, target highlight, and debug overlay."""
        annotated = frame.copy()
        h, w = frame.shape[:2]
        target = path[0] if path else None

        # Scale overlay elements by frame size
        scale = min(w, h) / REF_SIZE
        scale = max(scale, 0.5)
        pad = max(1, int(8 * scale))
        y0 = max(1, int(24 * scale))
        dy = max(1, int(18 * scale))
        font_state = max(0.3, round(0.5 * scale, 2))
        font_cmd = max(0.3, round(0.45 * scale, 2))
        font_fps = max(0.3, round(0.5 * scale, 2))
        font_bottom = max(0.3, round(0.4 * scale, 2))
        r_target = max(2, int(12 * scale))
        r_target_inner = max(1, int(6 * scale))
        r_ball = max(1, int(4 * scale))
        r_camera = max(1, int(6 * scale))
        line_thick = max(1, int(2 * scale))
        target_offset = int(28 * scale)

        # Balls: red circles; target ball: thick cyan ring + label
        for i, (cx, cy) in enumerate(path):
            is_target = (cx, cy) == target
            if is_target:
                cv2.circle(annotated, (cx, cy), r_target, (255, 255, 0), 3)
                cv2.circle(annotated, (cx, cy), r_target_inner, (255, 255, 0), -1)
                target_y = min(cy + target_offset, h - pad)
                target_x = max(0, cx - int(28 * scale))
                cv2.putText(
                    annotated,
                    "TARGET",
                    (target_x, target_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    font_state,
                    (255, 255, 0),
                    1,
                )
            else:
                cv2.circle(annotated, (cx, cy), r_ball, (0, 0, 255), -1)

        if len(path) >= 2:
            for i in range(len(path) - 1):
                cv2.line(annotated, path[i], path[i + 1], (0, 255, 0), line_thick)
        cv2.circle(annotated, camera_point, r_camera, (255, 255, 255), -1)

        # April tags: green circles + ID label (distinct from red balls / cyan target)
        r_tag = max(2, int(10 * scale))
        for (tx, ty, tag_id) in debug.april_tags:
            cx, cy = int(tx), int(ty)
            cv2.circle(annotated, (cx, cy), r_tag, (0, 255, 0), 2)
            label_y = max(r_tag + int(14 * scale), cy + int(14 * scale))
            label_y = min(label_y, h - pad)
            cv2.putText(
                annotated,
                str(tag_id),
                (cx - int(8 * scale), label_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_cmd,
                (0, 255, 0),
                1,
            )

        # Top-left: state, command, FPS|Loop (single panel, no overlap)
        panel_left_w = min(int(220 * scale), w - 2 * pad)
        panel_left_h = min(int(90 * scale), h - 2 * pad)
        roi_left = annotated[0:panel_left_h, 0:panel_left_w]
        overlay_left = roi_left.copy()
        cv2.rectangle(overlay_left, (0, 0), (panel_left_w, panel_left_h), (0, 0, 0), -1)
        annotated[0:panel_left_h, 0:panel_left_w] = cv2.addWeighted(
            overlay_left, 0.4, roi_left, 0.6, 0
        )
        cv2.putText(
            annotated,
            f"State: {debug.state_name}",
            (pad, y0),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_state,
            (0, 255, 255),
            1,
        )
        cv2.putText(
            annotated,
            f"Cmd: {debug.cmd_str}",
            (pad, y0 + dy),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_cmd,
            (0, 255, 200),
            1,
        )
        cv2.putText(
            annotated,
            f"FPS: {debug.fps:.1f} | Loop: {debug.loop_time_ms:.0f}ms",
            (pad, y0 + 2 * dy),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_fps,
            (0, 255, 255),
            1,
        )
        if debug.home_tag_info:
            cv2.putText(
                annotated,
                debug.home_tag_info,
                (pad, y0 + 3 * dy),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_cmd,
                (0, 255, 200),
                1,
            )

        # Bottom-left: balls, time remaining
        if debug.ball_count > 0 or debug.time_remaining > 0:
            cv2.putText(
                annotated,
                f"Balls: {debug.ball_count} | t: {debug.time_remaining:.0f}s",
                (pad, h - pad),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_bottom,
                (180, 180, 180),
                1,
            )

        return annotated
