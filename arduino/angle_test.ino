#include <Servo.h>

Servo steeringServo;
const int servoPin = 9;  // Connect servo signal wire to pin 9

const int minAngle = 0;
const int maxAngle = 180;
const int centerAngle = 90;

void setup() {
    Serial.begin(9600);
    steeringServo.attach(servoPin);
    steeringServo.write(centerAngle);  // Set servo to center position initially
}

void loop() {
    if (Serial.available()) {
        String input = Serial.readStringUntil('\n');
        if (input.startsWith("STEER:")) {
            int angle = input.substring(6).toInt();
            if (angle >= minAngle && angle <= maxAngle) {
                steeringServo.write(angle);
                Serial.print("Steering Angle Set To: ");
                Serial.println(angle);
            } else {
                Serial.println("Invalid Angle. Must be between 0 and 270.");
            }
        }
    }
}
