import cv2
import numpy as np
from picamera2 import Picamera2
from ultralytics import YOLO

# 1. Load the NCNN model folder
# Note: Use the 'task=detect' argument for NCNN models
model = YOLO('yolo11n_ncnn_model', task='detect')

# 2. Setup Camera Module 3
picam2 = Picamera2()
# Using 640x480 for a balance of speed and detection accuracy
config = picam2.create_video_configuration(main={'format': 'RGB888', 'size': (640, 480)})
picam2.configure(config)
picam2.start()

print("Robot Vision Started. Press 'q' in the window to quit.")

try:
    while True:
        # 3. Capture frame as a numpy array (RGB)
        frame = picam2.capture_array()
        
        # 4. Run YOLO Inference
        # imgsz=320 should match the export size for maximum speed
        # conf=0.4 filters out weak detections
        results = model(frame, imgsz=320, conf=0.4, verbose=False)
        
        # 5. Visualize
        # The .plot() method returns an image with boxes and labels
        annotated_frame = results[0].plot()
        
        # 6. Show the frame
        # Convert RGB to BGR for OpenCV display
        display_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR)
        cv2.imshow("UniBot Detection Feed", display_frame)
        
        # Check for 'q' key to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Always stop the camera and close windows cleanly
    picam2.stop()
    cv2.destroyAllWindows()