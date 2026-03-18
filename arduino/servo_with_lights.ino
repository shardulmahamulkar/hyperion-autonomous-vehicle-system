#include <Servo.h>

Servo myServo;
int servoPin = 9; // Servo control pin
int angle = 135;  // Default straight position
int stepSize = 5; // Step size for turning

int motorPWM = 5; // Motor PWM control pin
int pwmValue = 0; // Initial motor speed

// Relay Pins for RGB Lights
int relayBlue = 11;  // Blue light (Autonomous Mode)
int relayRed = 8;   // Red component
int relayGreen = 10; // Green component (Mixes with Red to make Yellow)

void setup() {
    Serial.begin(115200);
    myServo.attach(servoPin);
    myServo.write(angle); // Start with a straight servo
    
    pinMode(motorPWM, OUTPUT);
    analogWrite(motorPWM, pwmValue);

    pinMode(relayBlue, OUTPUT);
    pinMode(relayRed, OUTPUT);
    pinMode(relayGreen, OUTPUT);

    // Default: Manual Mode (Yellow = Red + Green ON)
    digitalWrite(relayBlue, LOW);
    digitalWrite(relayRed, HIGH);
    digitalWrite(relayGreen, HIGH);

    Serial.println("Arduino Initialized: Servo, Motor, and Lights Ready");
}

void loop() {
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n'); // Read full command
        command.trim();  // Remove any trailing newlines or spaces

        if (command == "R") {
            angle = min(angle + stepSize, 270);
            Serial.println("Turning Right");
        } 
        else if (command == "L") {
            angle = max(angle - stepSize, 0);
            Serial.println("Turning Left");
        }
        else if (command == "F") { // Reset to Straight Position
            angle = 180;
            Serial.println("Straightening Servo");
        }
        else if (command == "P") { // Increase PWM
            pwmValue = min(pwmValue + 10, 255);
            Serial.println("Increasing Speed");
        }
        else if (command == "S") { // Stop Immediately
            pwmValue = 0;
            Serial.println("Stopping: PWM set to 0");
        }
        else if (command == "REV") { // Reverse to recover from being stuck
            pwmValue = 100; // Reverse speed
            Serial.println("Reversing to recover from stall");
        }
        else if (command == "B") { // Enable Autonomous Mode (Blue Light ON, Yellow OFF)
            digitalWrite(relayBlue, HIGH);
            digitalWrite(relayRed, LOW);
            digitalWrite(relayGreen, LOW);
            Serial.println("Autonomous Mode Engaged (Blue ON, Yellow OFF)");
        }
        else if (command == "M") { // Enable Manual Mode (Yellow ON = Red + Green)
            digitalWrite(relayBlue, LOW);
            digitalWrite(relayRed, HIGH);
            digitalWrite(relayGreen, HIGH);
            Serial.println("Manual Mode Engaged (Yellow ON)");
        }
        else if (command == "X") { // Mission Complete (Green ON, Others OFF)
            digitalWrite(relayBlue, LOW);
            digitalWrite(relayRed, LOW);
            digitalWrite(relayGreen, HIGH);
            Serial.println("Mission Complete! (Green ON)");
        }
        else if (command == "O") { // Obstacle Detected (Red ON, Others OFF)
            digitalWrite(relayBlue, LOW);
            digitalWrite(relayRed, HIGH);
            digitalWrite(relayGreen, LOW);
            Serial.println("Obstacle Detected! (Red ON)");
        }
        else if (command == "C") { // Clear Obstacle (Back to Manual Mode - Yellow)
            digitalWrite(relayRed, HIGH);
            digitalWrite(relayGreen, HIGH);
            digitalWrite(relayBlue, LOW);
            Serial.println("Obstacle Cleared (Yellow ON)");
        }
        else if (command.startsWith("PWM:")) { // Handle PWM speed command
            pwmValue = command.substring(4).toInt();
            Serial.print("Setting Motor PWM: ");
            Serial.println(pwmValue);
        }
        else if (command == "0") {
            angle = max(0, 0);
            Serial.println("Turning Left");
        }
        else if (command == "U") { // Turn OFF all relays
            digitalWrite(relayBlue, LOW);
            digitalWrite(relayRed, LOW);
            digitalWrite(relayGreen, LOW);
            Serial.println("All Lights OFF");
        }

        myServo.write(angle);
        analogWrite(motorPWM, pwmValue);

        Serial.print("Servo Angle: ");
        Serial.println(angle);
        Serial.print("Motor PWM: ");
        Serial.println(pwmValue);
    }
}
