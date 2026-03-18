# Lane assist system for Infiniti 9.0 - won Best Autonomous Vehicle at SEVC
# Uses OpenCV edge detection, ROI masking, and Hough Transform for lane curvature

# ⚠️  CONFIGURATION — update these before running:
#   MODEL_PATH = path to your .pt model file
#   VIDEO_PATH = 0 for webcam, or path to a video file
#   SERIAL_PORT = your Arduino port (COM3 on Windows, /dev/ttyUSB0 on Linux)

if red_cones:
        ser.write(b"PWM:0\n")
        time.sleep(0.05)
        print("Sent to Arduino: PWM:0 (STOP)")

    elif yellow_cones or blue_cones:
        pwm_value = PWM_MAX if stuck_counter < STUCK_THRESHOLD else PWM_STUCK
        ser.write(f"PWM:{pwm_value}\n".encode())
        time.sleep(0.05)
        print(f"Sent to Arduino: PWM:{pwm_value}")


PWM_MAX = 255
PWM_STUCK = 100