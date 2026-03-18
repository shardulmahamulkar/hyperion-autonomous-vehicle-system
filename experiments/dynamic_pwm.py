# Experiment: dynamic PWM based on cone deviation from center

import os
import sys
import cv2
import numpy as np
import serial
import time
from ultralytics import YOLO

print("Starting in 10 seconds...")
# 10-second delay before execution

# Initialize Serial Communication with Arduino
try:
    arduino = serial.Serial("COM3", 9600, timeout=1)  # Change "COM3" to your Arduino port
    time.sleep(2)  # Give some time for the connection to initialize
except:
    print("ERROR: Could not connect to Arduino. Check the COM port.")
    arduino = None

# Define global paths
MODEL_PATH = "E:\\YOLOv8n\\yolov8n_.pt"
OUTPUT_PATH = "D:\\output2.mp4"
MIN_THRESH = 0.3

# Define ROI thresholds
ROI_Y_START = 0.5  # 50% of the screen for yellow/blue cones
ROI_RED = 0.3  # 30% of the screen for red cones

# Check if model file exists
if not os.path.exists(MODEL_PATH):
    print('WARNING: Model path is invalid or model was not found. Using default yolov8s.pt model instead.')
    MODEL_PATH = 'yolov8s.pt'

# Load YOLO model
model = YOLO(MODEL_PATH, task='detect')
labels = model.names       

if arduino:
    arduino.write(b'O')  # Initialize
    arduino.write(b'D')  # Debug
    arduino.write(b'B')  # Turn on blue LED
    
# Open camera
cap = cv2.VideoCapture("C:\\Users\\shard\\Downloads\\hehe.mp4")
if not cap.isOpened():
    print("ERROR: Camera not found. Exiting.")
    sys.exit(0)

# Get video properties
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))

# Initialize video writer
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(OUTPUT_PATH, fourcc, fps, (frame_width, frame_height))

# Bounding box colors
bbox_colors = {'y': (0, 255, 255), 'b': (255, 0, 0), 'r': (0, 0, 255)}

print("Processing video...")

roi_y_start_px = int(frame_height * ROI_Y_START)
roi_red_px = int(frame_height * ROI_RED)

# Define PWM limits
MAX_PWM = 102  # Moderate speed cap
MIN_PWM = 74   # Ensuring motor starts moving at 1.45V
STALL_PWM_THRESHOLD = 180   # Considered "high PWM"
STALL_TIME_THRESHOLD = 3     # Seconds before assuming the vehicle is stuck

# Tracking variables
last_move_time = time.time()
stuck = False

# Process each frame
frame_index = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Camera disconnected or error reading frame. Exiting.")
        break
    
    # Run YOLO inference
    results = model(frame, verbose=False)
    detections = results[0].boxes

    # Lists to store cone centers
    yellow_cones = []
    blue_cones = []
    red_detected = False

    for i in range(len(detections)):
        xyxy = detections[i].xyxy.cpu().numpy().squeeze().astype(int)
        xmin, ymin, xmax, ymax = xyxy
        center_x = (xmin + xmax) // 2
        center_y = (ymin + ymax) // 2
        classidx = int(detections[i].cls.item())
        classname = labels[classidx]
        conf = detections[i].conf.item()

        if conf > MIN_THRESH:
            if classname == "y" and center_y >= roi_y_start_px:
                yellow_cones.append((center_x, center_y))
                color = bbox_colors['y']
            elif classname == "b" and center_y >= roi_y_start_px:
                blue_cones.append((center_x, center_y))
                color = bbox_colors['b']
            elif classname == "r" and center_y >= roi_red_px:
                red_detected = True
                color = bbox_colors['r']
            else:
                continue

            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, 2)
            label = f"{classname}: {int(conf * 100)}%"
            cv2.putText(frame, label, (xmin, ymin - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    if red_detected:
        print("ALERT: RED CONE DETECTED! STOP!")
        if arduino:
            arduino.write(b'S')  # Stop PWM
    else:
        if yellow_cones or blue_cones:
            if arduino:
                arduino.write(b'P')  # Start PWM ramp-up

    # Calculate dynamic PWM
    if yellow_cones and blue_cones:
        lookahead_point = min(yellow_cones + blue_cones, key=lambda p: p[1])
        deviation = abs(lookahead_point[0] - frame_width // 2)
        normalized_deviation = deviation / (frame_width // 2)
        pwm_value = int(MAX_PWM - normalized_deviation * (MAX_PWM - MIN_PWM))
        
        # Ensure PWM is within limits
        pwm_value = max(MIN_PWM, min(pwm_value, MAX_PWM))
        
        # Send PWM
        pwm_command = f'PWM:{pwm_value}\n'
        if arduino:
            arduino.write(pwm_command.encode())
        print(f"Set PWM: {pwm_value}")

        # Detect if stuck
        if pwm_value > STALL_PWM_THRESHOLD:
            if time.time() - last_move_time > STALL_TIME_THRESHOLD:
                stuck = True
                print("🚨 Vehicle is STUCK! Trying to recover...")
                if arduino:
                    arduino.write(b'REV')  # Reverse or reset
            else:
                stuck = False
        else:
            last_move_time = time.time()

    out.write(frame)
    cv2.imshow('YOLO Detection', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Stopping early due to user input.")
        break
    
    frame_index += 1
    print(f"Processed frame {frame_index}", end='\r')

arduino.write(b'C')
if arduino:
    arduino.write(b'X')  # Turn off blue LED

cap.release()
out.release()
cv2.destroyAllWindows()
print(f"\nOutput video saved as {OUTPUT_PATH}")

if arduino:
    arduino.write(b'G')
    time.sleep(10)
if arduino:
    arduino.write(b'I')
