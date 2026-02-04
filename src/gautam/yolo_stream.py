import cv2
from ultralytics import YOLO

# =========================
# STREAM CONFIG
# =========================
PI_IP = "172.20.10.5"
STREAM0 = f"http://{PI_IP}:8080/?action=stream"   # /dev/video0
STREAM1 = f"http://{PI_IP}:8081/?action=stream"   # /dev/video2

MODEL_PATH = "last.pt"
CONF_THRESHOLD = 0.5

WIN0 = "YOLO Annotated - Stream 8080 (video0)"
WIN1 = "YOLO Annotated - Stream 8081 (video2)"

# =========================
# LOAD YOLO MODEL
# =========================
model = YOLO(MODEL_PATH)

# Use GPU if available (else CPU)
try:
    model.to("cuda")
except Exception:
    model.to("cpu")

# =========================
# OPEN BOTH STREAMS
# =========================
cap0 = cv2.VideoCapture(STREAM0)
cap1 = cv2.VideoCapture(STREAM1)

if not cap0.isOpened():
    print("❌ Failed to open stream 8080")
    raise SystemExit(1)

if not cap1.isOpened():
    print("❌ Failed to open stream 8081")
    raise SystemExit(1)

print("✅ Both streams opened")

# =========================
# CREATE WINDOWS
# =========================
cv2.namedWindow(WIN0, cv2.WINDOW_NORMAL)
cv2.namedWindow(WIN1, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WIN0, 960, 720)
cv2.resizeWindow(WIN1, 960, 720)

# =========================
# MAIN LOOP
# =========================
while True:
    ret0, frame0 = cap0.read()
    ret1, frame1 = cap1.read()

    # If either stream drops a frame, just skip that iteration
    if not ret0 or frame0 is None or not ret1 or frame1 is None:
        continue

    # -------------------------
    # YOLO on stream 8080
    # -------------------------
    res0 = model(frame0, conf=CONF_THRESHOLD, verbose=False)
    ann0 = res0[0].plot()

    # -------------------------
    # YOLO on stream 8081
    # -------------------------
    res1 = model(frame1, conf=CONF_THRESHOLD, verbose=False)
    ann1 = res1[0].plot()

    # -------------------------
    # DISPLAY
    # -------------------------
    cv2.imshow(WIN0, ann0)
    cv2.imshow(WIN1, ann1)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# =========================
# CLEANUP
# =========================
cap0.release()
cap1.release()
cv2.destroyAllWindows()

