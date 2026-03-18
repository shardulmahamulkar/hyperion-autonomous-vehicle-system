# Cone detection integrated with LED light system on Infiniti 9.0

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
    arduino = serial.Serial("COM3", 115200, timeout=1)  # Change "COM3" to your Arduino port
    time.sleep(2)  # Give some time for the connection to initialize
except:
    print("ERROR: Could not connect to Arduino. Check the COM port.")
    arduino = None

# Define global paths
MODEL_PATH = "E:\\YOLOv8n\\yolov8n_.pt"
OUTPUT_PATH = "D:\\output2.mp4"
MIN_THRESH = 0.3

# Define ROI thresholds
ROI_Y_START = 0.5  # 1% of the screen for yellow/blue cones
ROI_RED = 0.3  # 30% of the screen for red cones

# Check if model file exists
if not os.path.exists(MODEL_PATH):
    print('WARNING: Model path is invalid or model was not found. Using default yolov8s.pt model instead.')
    MODEL_PATH = 'yolov8s.pt'

# Load YOLO model
model = YOLO(MODEL_PATH, task='detect')
labels = model.names       
arduino.write(b'O')

if arduino:
    arduino.write(b'D')
    arduino.write(b'B')  # Turn on blue LED
    

# Open camera (using 0 for default webcam or a different integer for other connected cameras)
cap = cv2.VideoCapture("C:\\Users\\shard\\Downloads\\hehe.mp4")  # Use 0 for default camera or change it if you have multiple cameras

if not cap.isOpened():
    print("ERROR: Camera not found. Exiting.")
    sys.exit(0)

# Get video properties
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))

# Initialize video writer for saving output (if needed)
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(OUTPUT_PATH, fourcc, fps, (frame_width, frame_height))

# Bounding box colors
bbox_colors = {'y': (0, 255, 255), 'b': (255, 0, 0), 'r': (0, 0, 255)}

print("Processing video...")

roi_y_start_px = int(frame_height * ROI_Y_START)
roi_red_px = int(frame_height * ROI_RED)

# Function to connect cones of the same color
def connect_cones(cones, color):
    if len(cones) > 1:
        cones.sort(key=lambda c: c[1])  # Sort by Y (bottom to top)
        for i in range(len(cones) - 1):
            cv2.line(frame, cones[i], cones[i + 1], color, 2)

# Function to generate and visualize the path using centroids
def generate_path(yellow_cones, blue_cones):
    centroids = []

    # Create midpoints between left (yellow) and right (blue) cones
    for y, b in zip(yellow_cones, blue_cones):
        centroid_x = (y[0] + b[0]) // 2
        centroid_y = (y[1] + b[1]) // 2
        centroids.append((centroid_x, centroid_y))

    # Find the lowest detected centroid (highest Y value)
    if centroids:
        lowest_centroid = max(centroids, key=lambda p: p[1])  # Get centroid with max Y value
        start_point = (frame_width // 2, frame_height)  # Bottom center

        # Draw a line from the bottom center to the lowest centroid
        cv2.line(frame, start_point, lowest_centroid, (0, 0, 255), 2)

    # Draw the remaining path
    if len(centroids) > 1:
        for i in range(len(centroids) - 1):
            cv2.line(frame, centroids[i], centroids[i + 1], (0, 0, 255), 2)  # Return centroids for steering logic
    return centroids

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

    # Process detections
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

            # Draw bounding box
            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, 2)
            label = f"{classname}: {int(conf * 100)}%"
            cv2.putText(frame, label, (xmin, ymin - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    if red_detected:
        print("ALERT: RED CONE DETECTED! STOP!")
        cv2.putText(frame, "STOPPING: RED CONE DETECTED!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        if arduino:
            arduino.write(b'S')  # Stop PWM immediately
    else:
        if yellow_cones or blue_cones:
            if arduino:
                arduino.write(b'P')  # Start PWM ramp-up

    # Generate path and get centroids
    centroids = generate_path(yellow_cones, blue_cones)

    # Add a red dot 100 pixels above the bottom center
    dot_x = frame_width // 2
    dot_y = frame_height - 100
    cv2.circle(frame, (dot_x, dot_y), 5, (0, 0, 0), 1)  # Draw red dot

    # Find closest path point at the dot's Y level
    if centroids:
        closest_point = min(centroids, key=lambda p: abs(p[1] - dot_y))

        # Determine steering direction based on dot's position relative to the path
        if dot_x < closest_point[0]:  # Dot is left of the path
            if arduino:
                arduino.write(f"R\n".encode())  # Turn right
            print("TURNING RIGHT")
        elif dot_x > closest_point[0]:  # Dot is right of the path
            if arduino:
                arduino.write(b'L')  # Turn left
            print("TURNING LEFT")

    # **New Condition: When only one type of cone is detected**
    if yellow_cones and not blue_cones:  # Only yellow cones detected
        if arduino:
            arduino.write(b'R')  # Turn right
        print("ONLY YELLOW CONES DETECTED: TURNING RIGHT")

    elif blue_cones and not yellow_cones:  # Only blue cones detected
        if arduino:
            arduino.write(b'L')  # Turn left
        print("ONLY BLUE CONES DETECTED: TURNING LEFT")

    # Write the processed frame to the output video
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
