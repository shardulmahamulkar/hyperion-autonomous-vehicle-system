# Cone detection with exponential smoothing on steering angle
# Reduces servo jitter caused by noisy detections

# ⚠️  CONFIGURATION — update these before running:
#   MODEL_PATH = path to your .pt model file
#   VIDEO_PATH = 0 for webcam, or path to a video file
#   SERIAL_PORT = your Arduino port (COM3 on Windows, /dev/ttyUSB0 on Linux)

import os
import sys
import cv2
import numpy as np
import serial
from ultralytics import YOLO
import time

# Define global paths
MODEL_PATH = "E:\\YOLOv8n\\yolov8n_.pt"
VIDEO_PATH = "C:\\Users\\shard\\Downloads\\hehe.mp4"
OUTPUT_PATH = "D:\\output2.mp4"
MIN_THRESH = 0.1
ROI_Y_START = 0.5

# Serial communication setup
SERIAL_PORT = "COM3"
BAUD_RATE = 9600
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
except Exception as e:
    print(f"ERROR: Could not open serial port {SERIAL_PORT}: {e}")
    sys.exit(0)

# Check if model file exists
if not os.path.exists(MODEL_PATH):
    print('WARNING: Model path is invalid or model was not found. Using default yolov8s.pt model instead.')
    MODEL_PATH = 'yolov8s.pt'

# Check if video file exists
if not os.path.isfile(VIDEO_PATH):
    print(f'ERROR: Video file "{VIDEO_PATH}" not found. Exiting.')
    sys.exit(0)

# Load YOLO model
model = YOLO(MODEL_PATH, task='detect')
labels = model.names

# Open video file
cap = cv2.VideoCapture(VIDEO_PATH)

# Get video properties
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# Initialize video writer
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(OUTPUT_PATH, fourcc, fps, (frame_width, frame_height))

bbox_colors = {'y': (0, 255, 255), 'b': (255, 0, 0), 'r': (0, 0, 255)}
frame_index = 0
roi_y_start_px = int(frame_height * ROI_Y_START)

# Movement tracking variables
prev_centroid = None
stuck_counter = 0
PWM_NORMAL = 255
PWM_JERK = 255
STUCK_THRESHOLD = 10

# Steering variables
STEERING_CENTER = 90
STEERING_LEFT = 0
STEERING_RIGHT = 180
STEERING_UPDATE_RATE = 0.1
ANGLE_THRESHOLD = 1  # Ignore changes below this threshold
SMOOTHING_FACTOR = 0.5  # Exponential smoothing factor
MAX_ANGLE_JUMP = 30  # Ignore extreme jumps in angles unless only one cone color is seen
last_steering_time = time.time()
current_steering_angle = STEERING_CENTER

print("Processing video...")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Reached the end of the video.")
        break

    results = model(frame, verbose=False)
    detections = results[0].boxes

    yellow_cones, blue_cones, red_cones = [], [], []
    for i in range(len(detections)):
        xyxy = detections[i].xyxy.cpu().numpy().squeeze().astype(int)
        xmin, ymin, xmax, ymax = xyxy
        center_x = (xmin + xmax) // 2
        center_y = (ymin + ymax) // 2
        
        if center_y < roi_y_start_px:
            continue

        classidx = int(detections[i].cls.item())
        classname = labels[classidx]
        conf = detections[i].conf.item()

        if conf > MIN_THRESH:
            if classname == "y":
                yellow_cones.append((center_x, center_y))
                color = bbox_colors['y']
            elif classname == "b":
                blue_cones.append((center_x, center_y))
                color = bbox_colors['b']
            elif classname == "r":
                red_cones.append((center_x, center_y))
                color = bbox_colors['r']
            else:
                continue

            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, 2)
            label = f"{classname}: {int(conf * 100)}%"
            cv2.putText(frame, label, (xmin, ymin - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    if red_cones:
        command = f"PWM:0\n"
        ser.write(command.encode())
        print(f"Sent to Arduino: {command.strip()}")
        print("Red cone detected! Stopping vehicle.")
    
    if yellow_cones and not blue_cones:
        current_steering_angle = STEERING_RIGHT
    
    elif blue_cones and not yellow_cones:
        current_steering_angle = STEERING_LEFT
    
    def generate_path(yellow_cones, blue_cones):
        centroids = []
        for y, b in zip(yellow_cones, blue_cones):
            centroid_x = (y[0] + b[0]) // 2
            centroid_y = (y[1] + b[1]) // 2
            centroids.append((centroid_x, centroid_y))
        
        if centroids:
            lowest_centroid = max(centroids, key=lambda p: p[1])
            start_point = (frame_width // 2, frame_height)
            cv2.line(frame, start_point, lowest_centroid, (0, 0, 255), 2)
        
        return lowest_centroid if centroids else None

    centroid = generate_path(yellow_cones, blue_cones)

    if centroid and time.time() - last_steering_time >= STEERING_UPDATE_RATE:
        new_steering_angle = int(np.clip((centroid[0] / frame_width) * 180, STEERING_LEFT, STEERING_RIGHT))
        angle_change = abs(new_steering_angle - current_steering_angle)

        if angle_change > ANGLE_THRESHOLD and (angle_change < MAX_ANGLE_JUMP or not (yellow_cones and blue_cones)):
            current_steering_angle = int(SMOOTHING_FACTOR * new_steering_angle + (1 - SMOOTHING_FACTOR) * current_steering_angle)
            command = f"STEER:{current_steering_angle}\n"
            ser.write(command.encode())
            print(f"Sent to Arduino: {command.strip()}")
            last_steering_time = time.time()

    out.write(frame)
    cv2.imshow('YOLO Detection', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Stopping early due to user input.")
        break

cap.release()
out.release()
cv2.destroyAllWindows()
ser.close()
print(f"\nOutput video saved as {OUTPUT_PATH}")
