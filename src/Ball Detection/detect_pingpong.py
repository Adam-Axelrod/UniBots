import cv2
import numpy as np
from picamera2 import Picamera2
from ultralytics import YOLO

# 1. Load your NCNN optimized model
model = YOLO('yolo11n_ncnn_model', task='detect')

# 2. Setup Camera Module 3 (High speed, 320x320 resolution)
picam2 = Picamera2()
config = picam2.create_video_configuration(main={'format': 'RGB888', 'size': (320, 320)})
picam2.configure(config)
picam2.start()

FRAME_CENTER_X = 160  # Half of 320px width

print("Tracking Mode Active. Center X target is 160.")

try:
    while True:
        frame = picam2.capture_array()
        
        # classes=[32] filters for 'sports ball' only (COCO class for ping pong balls)
        results = model(frame, imgsz=320, conf=0.3, classes=[32], verbose=False)
        
        best_ball = None
        max_conf = 0

        # 3. Find the most confident ball in the frame
        for r in results:
            for box in r.boxes:
                conf = box.conf[0].item()
                if conf > max_conf:
                    max_conf = conf
                    # Get box center
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    best_ball = (int((x1 + x2) / 2), int((y1 + y2) / 2))

        # 4. Calculate Steering Error
        if best_ball:
            ball_x, ball_y = best_ball
            error_x = ball_x - FRAME_CENTER_X
            
            # Positive = Ball is to the right (Turn Right)
            # Negative = Ball is to the left (Turn Left)
            print(f"Ball Found! Center X: {ball_x} | Steering Error: {error_x}")
            
            # Visualization
            cv2.circle(frame, (ball_x, ball_y), 10, (0, 255, 0), -1)
            cv2.line(frame, (FRAME_CENTER_X, 0), (FRAME_CENTER_X, 320), (255, 0, 0), 1)
        else:
            print("Searching for ball...")

        # 5. Display (optional - disable in match to save 10% CPU)
        display_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imshow("Tracking View", display_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    picam2.stop()
    cv2.destroyAllWindows()