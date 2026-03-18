#include <Servo.h>

Servo myServo;
const int servoPin = 9;  // Connect servo signal wire to pin 9

const int minAngle = 0;
const int maxAngle = 270;
const int centerAngle = 135;
int currentAngle = centerAngle;  // Maintain the last valid angle

void setup() {
    Serial.begin(9600);
    myServo.attach(servoPin);
    myServo.write(currentAngle);  // Set servo to center position initially
}

void loop() {
    if (Serial.available()) {
        int angle = Serial.parseInt();
        while (Serial.available()) Serial.read(); // Clear buffer

        if (angle >= minAngle && angle <= maxAngle) {
            currentAngle = angle;  // Store last valid angle
            myServo.write(currentAngle);
            Serial.print("Steering Angle Set To: ");
            Serial.println(currentAngle);
        } else if (angle != 0) {  // Ignore accidental 0 readings
            Serial.println("Invalid Angle. Must be between 0 and 270.");
        }
    }
}
