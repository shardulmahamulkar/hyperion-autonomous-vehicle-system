# Autonomous Vehicle System — STES Hyperion

> Built for the Solar Electric Vehicle Championship (SEVC/ESVC) — won **Best Autonomous Vehicle** and **India Rank 2** at SEVC Coimbatore, **Asia Rank 2** at ESVC Noida.

Two vehicles. Two systems. One codebase.

---

## Vehicles

| Vehicle | System | Result |
|---|---|---|
| **Infiniti 9.0** | Lane assist + Collision detection |  India Rank 2 — SEVC Best Autonomous Vehicle — SEVC |
| **Ananta** | Cone detection + Path planning |  Asia Rank 2 — ESVC |

---

## What it does

The system gives a solar-powered vehicle the ability to:
- Follow a lane using only a webcam and OpenCV
- Detect traffic cones and navigate between them
- Avoid collisions using real-time frame analysis
- Control steering (servo) and rear wheel drive (motor) autonomously

---

## System Architecture

```
Webcam
  │
  ▼
Frame capture (OpenCV)
  │
  ├──▶ Lane Detection Pipeline
  │       Edge detection → ROI masking → Hough Transform → curvature estimation
  │
  ├──▶ Cone Detection Pipeline (YOLOv5/YOLOv8)
  │       Inference → bounding boxes → path geometry calculation
  │
  └──▶ Collision Detection
          Frame diff / proximity threshold
  │
  ▼
Control Logic
  │
  ├──▶ Serial commands → Arduino Uno → Servo motor (steering)
  └──▶ PWM signal → Arduino Uno → Rear wheel motor (throttle)
```

---

## Lane Assist (Infiniti 9.0)

Built using classical computer vision — no ML model needed for lane following.

**Pipeline:**
1. Capture frame from webcam
2. Convert to grayscale → Gaussian blur
3. Canny edge detection
4. Apply ROI mask to isolate road area
5. Hough Line Transform to detect lane lines
6. Calculate lane curvature and center offset
7. Map offset to steering angle → send via serial to Arduino

**Collision detection** runs in parallel — monitors frame changes and proximity thresholds to trigger emergency stop.

---

## Cone Detection (Ananta)

Trained on a custom dataset for real-world track conditions.

**Dataset:**
- ~13,000 images total
- 24GB raw data sourced from FOSCО dataset
- ~1,000 images manually annotated by the team
- Trained on Google Colab (no GPU available locally)

**Model:** YOLOv5 → upgraded to YOLOv8  
**Accuracy:** ~91% detection  
**Inference speed:** 10–15 FPS on vehicle laptop hardware

**Path planning:**  
Cone positions from YOLO bounding boxes → custom geometry to calculate midpoint path → steering angle derived from path curvature → serial command to Arduino.

---

## Hardware

| Component | Detail |
|---|---|
| Camera | Standard USB webcam (primary) |
| Compute | Laptop (onboard) |
| Microcontroller | Arduino Uno |
| Steering | Servo motor via PWM |
| Drive | Rear wheel motor via PWM |
| Attempted | Raspberry Pi + ArduCam — too slow for real-time inference, switched to laptop |

> The RPi couldn't handle real-time inference fast enough for vehicle control — switching to a laptop dropped latency significantly and stabilized the control loop.

---

## Tech Stack

- **Python** — core logic
- **OpenCV** — lane detection, frame processing
- **YOLOv5 / YOLOv8** — cone detection
- **Google Colab** — model training
- **Arduino Uno** — hardware control
- **PySerial** — laptop ↔ Arduino communication
- **Raspberry Pi** — attempted, replaced

---
#  Disclaimer — Read Before Running

This code was written under competition conditions. It worked on our specific hardware setup during the championship. It may or may not work for you depending on your setup.

---

##  What will definitely need changing:

- **MODEL_PATH** — the `.pt` model file is not included (too large). You'll need to train your own or use a generic YOLOv8 model  
- **VIDEO_PATH** — hardcoded to a local file path. Change to `0` for webcam  
- **SERIAL_PORT** — hardcoded to `COM3` (Windows). Change to `/dev/ttyUSB0` or similar on Linux  
- **Arduino wiring** — servo and motor pin assignments may differ from your setup  

---

##  What probably works fine:

- The OpenCV lane detection pipeline (no model needed)  
- The YOLO inference logic if you supply your own model  
- The Arduino serial communication protocol  
- The path planning geometry  

---

##  What's messy and why:

- Multiple versions of the same script exist in `/experiments` — these are iterations we tested at different stages. The final versions are in `/cone_detection` and `/lane_assist`  
- Some scripts have `hehe.mp4` as the video path — that was our test footage, obviously not included  
- `experiments/breakeven_analysis.py` is completely unrelated — it's an EV cost model from another task that ended up in the same folder somehow  
- Variable names in some files are... creative. We were debugging at 2am before the competition  

---

##  Hardware specific:

- PWM values (`MIN_PWM`, `MAX_PWM`) are tuned for our specific motor. You'll likely need to recalibrate  
- Steering angle range (0–180°) is specific to our servo. Adjust `MAX_LEFT`, `MAX_RIGHT`, `CENTER_ANGLE` accordingly  
- The smoothing factor (`SMOOTHING_FACTOR = 0.5`) was empirically tuned on our track — faster tracks may need a lower value  

---

## Models not included because:

The trained `.pt` model files are too large for GitHub. The `data.yaml` and a few sample training images are included so you can see the dataset structure.

To reproduce, train **YOLOv8n** on a cone dataset with classes:
- `y` (yellow)
- `b` (blue)
- `r` (red)

---

## Team

Built by a core team of 3 as part of STES Hyperion's solar vehicle program.  
CV/software system designed and implemented by me.

---

## Competition Results

-  **Best Autonomous Vehicle** — Solar Electric Vehicle Championship (SEVC), Coimbatore — Mar 2025
-  **India Rank 2** — Solar Electric Vehicle Championship (SEVC), Coimbatore — Mar 2025  
-  **Asia Rank 2** — Electric Solar Vehicle Championship (ESVC), Noida — Apr 2025
