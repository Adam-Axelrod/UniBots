# UniBots | 2025-2026 Season
Ball detection via http which uses YOLOv8 to detect ping pong balls in real time and places bounding boxes over them with a confidence ratio as well.Also greedy graph connects the ball which shows expected path planned.

## Instructions

### 1. Install ustreamer on the pi to stream via pi 
`sudo apt update`

`sudo apt install ustreamer`

### 2. Run ustreamer from the pi
`ustreamer --device=/dev/video0 --resolution=640x480 --desired-fps=30 --host=0.0.0.0 --port=8080`


### 3. Install on laptop

`pip install ultralytics opencv-python`

### 4. Run yolo code on laptop
`cd src/gautam`

`python3 yolo_stream.py`

