# Experiment: dynamic PWM combined with servo steering

import os
import sys
import cv2
import numpy as np
import serial
import time
from ultralytics import YOLO

def generate_path(yellow_cones, blue_cones):
    centroids = yellow_cones + blue_cones
    centroids.sort(key=lambda p: p[1])  # Sort by Y position (bottom to top)
    return centroids

def debug_log(message):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

print("Starting in 10 seconds...")

try:
    arduino = serial.Serial("COM3", 9600, timeout=1)
    time.sleep(2)
    debug_log("Arduino connected successfully.")
except:
    debug_log("ERROR: Could not connect to Arduino. Check the COM port.")
    arduino = None

MODEL_PATH = "E:\\YOLOv8n\\yolov8n_.pt"
OUTPUT_PATH = "D:\\output2.mp4"
MIN_THRESH = 0.3

ROI_Y_START = 0.5
ROI_RED = 0.3

MAX_PWM = 90
MIN_PWM = 74
STALL_PWM_THRESHOLD = 150
STALL_TIME_THRESHOLD = 3
last_move_time = time.time()
stuck = False

if not os.path.exists(MODEL_PATH):
    debug_log('WARNING: Model path is invalid. Using default yolov8s.pt.')
    MODEL_PATH = 'yolov8s.pt'

model = YOLO(MODEL_PATH, task='detect')
labels = model.names

if arduino:
    arduino.write(b'O')
    arduino.write(b'D')
    arduino.write(b'B')
    debug_log("Sent initialization commands to Arduino.")

cap = cv2.VideoCapture("C:\\Users\\shard\\Downloads\\hehe.mp4")
if not cap.isOpened():
    debug_log("ERROR: Camera not found. Exiting.")
    sys.exit(0)

frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

roi_y_start_px = int(frame_height * ROI_Y_START)
roi_red_px = int(frame_height * ROI_RED)

arduino.write(b'F')
debug_log("Processing video...")
frame_index = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        debug_log("Camera disconnected or error reading frame. Exiting.")
        break
    
    results = model(frame, verbose=False)
    detections = results[0].boxes


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
            elif classname == "b" and center_y >= roi_y_start_px:
                blue_cones.append((center_x, center_y))
            elif classname == "r" and center_y >= roi_red_px:
                red_detected = True

    if red_detected:
        debug_log("ALERT: RED CONE DETECTED! STOP!")
        if arduino:
            arduino.write(b'S')
    else:
        if yellow_cones or blue_cones:
            if arduino:
                arduino.write(b'P')
    
    centroids = generate_path(yellow_cones, blue_cones)
    dot_x = frame_width // 2
    dot_y = frame_height - 100
    cv2.circle(frame, (dot_x, dot_y), 5, (0, 0, 0), 1)

    if centroids:
        closest_point = min(centroids, key=lambda p: abs(p[1] - dot_y))
        if dot_x < closest_point[0]:
            debug_log("TURNING RIGHT")
            if arduino:
                arduino.write(b'R')
        elif dot_x > closest_point[0]:
            debug_log("TURNING LEFT")
            if arduino:
                arduino.write(b'L')
    
    if yellow_cones and not blue_cones:
        debug_log("ONLY YELLOW CONES DETECTED: TURNING RIGHT")
        if arduino:
            arduino.write(b'R')
    elif blue_cones and not yellow_cones:
        debug_log("ONLY BLUE CONES DETECTED: TURNING LEFT")
        if         arduino:
            arduino.write(b'L')
    
    if yellow_cones or blue_cones:
        lookahead_point = min(yellow_cones + blue_cones, key=lambda p: p[1])
        deviation = abs(lookahead_point[0] - frame_width // 2)
        normalized_deviation = deviation / (frame_width // 2)
        pwm_value = int(MAX_PWM - normalized_deviation * (MAX_PWM - MIN_PWM))
        pwm_value = max(MIN_PWM, min(pwm_value, MAX_PWM))
        pwm_command = f'PWM:{pwm_value}\n'
        if arduino:
            arduino.write(pwm_command.encode())
        debug_log(f"Set PWM: {pwm_value}")
        
        if pwm_value > STALL_PWM_THRESHOLD:
            if time.time() - last_move_time > STALL_TIME_THRESHOLD:
                stuck = True
                debug_log("\U0001F6A8 Vehicle is STUCK! Trying to recover...")
                if arduino:
                    arduino.write(b'REV')
            else:
                stuck = False
        else:
            last_move_time = time.time()
    
    cv2.imshow('YOLO Detection', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        debug_log("Stopping early due to user input.")
        break
    
    frame_index += 1
    debug_log(f"Processed frame {frame_index}")

arduino.write(b'U')
if arduino:

    arduino.write(b'X')
    time.sleep(10)
    arduino.write(b'U')
cap.release()
cv2.destroyAllWindows()
debug_log(f"\nOutput video saved as {OUTPUT_PATH}")
if arduino: 
    arduino.write(b'C')