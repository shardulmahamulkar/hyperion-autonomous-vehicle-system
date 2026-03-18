# Visualization only - no Arduino control
# Used for testing cone detection and path generation logic on video

import os
import sys
import cv2
import numpy as np
from ultralytics import YOLO

# Define global paths
MODEL_PATH = "E:\\YOLOv8n\\yolov8n_.pt"
VIDEO_PATH = "C:\\Users\\shard\\Downloads\\hehe.mp4"
OUTPUT_PATH = "D:\\output2.mp4"
MIN_THRESH = 0.1
ROI_Y_START = 0.5  # Lower 50% of the screen

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

# Bounding box colors
bbox_colors = {'y': (0, 255, 255), 'b': (255, 0, 0)}

print("Processing video...")
frame_index = 0
roi_y_start_px = int(frame_height * ROI_Y_START)  # Convert ROI percentage to pixels

# Process each frame
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Reached the end of the video.")
        break

    # Run YOLO inference
    results = model(frame, verbose=False)
    detections = results[0].boxes

    # Lists to store cone centers
    yellow_cones = []
    blue_cones = []

    # Process detections
    for i in range(len(detections)):
        xyxy = detections[i].xyxy.cpu().numpy().squeeze().astype(int)
        xmin, ymin, xmax, ymax = xyxy
        center_x = (xmin + xmax) // 2
        center_y = (ymin + ymax) // 2

        # Ignore cones outside the lower 50% of the frame
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
            else:
                continue

            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, 2)
            label = f"{classname}: {int(conf * 100)}%"
            cv2.putText(frame, label, (xmin, ymin - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # Function to connect cones by the nearest Y-axis neighbor
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
                cv2.line(frame, centroids[i], centroids[i + 1], (0, 0, 255), 2)

    # Connect yellow and blue cones
    connect_cones(yellow_cones, bbox_colors['y'])
    connect_cones(blue_cones, bbox_colors['b'])
    generate_path(yellow_cones, blue_cones)

    # Write the processed frame to the output video
    out.write(frame)
    cv2.imshow('YOLO Detection', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Stopping early due to user input.")
        break

    frame_index += 1
    print(f"Processed frame {frame_index}/{frame_count}", end='\r')

cap.release()
out.release()
cv2.destroyAllWindows()
print(f"\nOutput video saved as {OUTPUT_PATH}")
