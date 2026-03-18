# Simple Arduino LED test utility
# Commands: B (Blue), Y (Yellow), G (Green), R (Red)

import serial
import time

# Replace 'COM3' with your Arduino's port (e.g., '/dev/ttyUSB0' for Linux, 'COMx' for Windows)
arduino_port = "COM3"  
baud_rate = 9600  

try:
    # Establish connection to Arduino
    arduino = serial.Serial(arduino_port, baud_rate, timeout=1)
    time.sleep(2)  # Wait for Arduino to initialize

    print("Connected to Arduino.")
    print("Commands: B (Blue), Y (Yellow), G (Green for 10s), R (Red), OFF_B, OFF_Y, OFF_R")
    
    while True:
        cmd = input("Enter command: ").strip().upper()  # Get user input
        
        if cmd in ["B", "Y", "G", "R", "OFF_B", "OFF_Y", "OFF_R"]:
            arduino.write((cmd + "\n").encode())  # Send command to Arduino
            print(f"Sent: {cmd}")
        elif cmd == "EXIT":
            print("Exiting program.")
            break
        else:
            print("Invalid command. Try again.")

except serial.SerialException:
    print("⚠️ Error: Could not connect to Arduino. Check the port and try again.")

finally:
    if 'arduino' in locals():
        arduino.close()
