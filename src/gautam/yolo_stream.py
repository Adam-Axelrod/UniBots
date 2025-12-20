import cv2
import math
from ultralytics import YOLO

PI_IP = "10.42.0.117"   
STREAM_URL = f"http://{PI_IP}:8080/?action=stream"
MODEL_PATH = "last.pt"

CONF_THRESHOLD = 0.5

WINDOW_NAME = "YOLO Ping Pong Greedy Path"

# =========================
# LOAD YOLO MODEL
# =========================
model = YOLO(MODEL_PATH)
model.to("cuda")  # GPU inference

# =========================
# OPEN VIDEO STREAM
# =========================
cap = cv2.VideoCapture(STREAM_URL)

if not cap.isOpened():
    print("❌ Failed to open video stream")
    exit(1)

print("✅ Video stream opened")

# =========================
# CREATE FULLSCREEN WINDOW
# =========================
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(
    WINDOW_NAME,
    cv2.WND_PROP_FULLSCREEN,
    cv2.WINDOW_FULLSCREEN
)

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    h, w, _ = frame.shape
    camera_point = (w // 2, h)  # bottom-center of image

    # -------------------------
    # YOLO INFERENCE
    # -------------------------
    results = model(frame, conf=CONF_THRESHOLD, verbose=False)
    annotated = results[0].plot()

    # -------------------------
    # COLLECT BALL CENTERS
    # -------------------------
    centers = []

    for box in results[0].boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)
        centers.append((cx, cy))

    # Draw detected ball centers
    for (cx, cy) in centers:
        cv2.circle(annotated, (cx, cy), 4, (0, 0, 255), -1)

    # -------------------------
    # GREEDY NEAREST PATH
    # -------------------------
    if len(centers) >= 1:
        remaining = centers.copy()
        path = []

        # Start from ball closest to camera
        start = min(
            remaining,
            key=lambda p: math.hypot(
                p[0] - camera_point[0],
                p[1] - camera_point[1]
            )
        )

        path.append(start)
        remaining.remove(start)

        # Greedy chaining
        while remaining:
            last = path[-1]
            next_ball = min(
                remaining,
                key=lambda p: math.hypot(
                    p[0] - last[0],
                    p[1] - last[1]
                )
            )
            path.append(next_ball)
            remaining.remove(next_ball)

        # Draw path edges
        for i in range(len(path) - 1):
            cv2.line(
                annotated,
                path[i],
                path[i + 1],
                (0, 255, 0),
                2
            )

        # Highlight start node (closest to camera)
        cv2.circle(annotated, path[0], 7, (255, 0, 0), -1)

        # Optional: draw camera reference
        cv2.circle(annotated, camera_point, 6, (255, 255, 255), -1)

    # -------------------------
    # DISPLAY (FULLSCREEN)
    # -------------------------
    cv2.imshow(WINDOW_NAME, annotated)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# =========================
# CLEANUP
# =========================
cap.release()
cv2.destroyAllWindows()

