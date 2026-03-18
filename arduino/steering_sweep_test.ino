#include <Servo.h>

#define MOTOR_PIN 9  // PWM pin for motor speed
#define STEERING_PIN 10 // Servo pin for steering

Servo steeringServo;
int motorSpeed = 0;
int steeringAngle = 90; // Default straight position
int currentSteeringAngle = 90; // Track the current servo position

void setup() {
    Serial.begin(9600);
    steeringServo.attach(STEERING_PIN);
    pinMode(MOTOR_PIN, OUTPUT);
    analogWrite(MOTOR_PIN, motorSpeed); // Start with motor off
    steeringServo.write(steeringAngle); // Center the steering
}

void sweepSteering(int targetAngle) {
    if (targetAngle > currentSteeringAngle) {
        for (int angle = currentSteeringAngle; angle <= targetAngle; angle++) {
            steeringServo.write(angle);
            delay(10); // Adjust for smoother movement
        }
    } else {
        for (int angle = currentSteeringAngle; angle >= targetAngle; angle--) {
            steeringServo.write(angle);
            delay(10); // Adjust for smoother movement
        }
    }
    currentSteeringAngle = targetAngle;
}

void loop() {
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n');
        command.trim();

        if (command.startsWith("PWM:")) {
            motorSpeed = command.substring(4).toInt();
            analogWrite(MOTOR_PIN, motorSpeed);
            Serial.print("Motor Speed Set to: ");
            Serial.println(motorSpeed);
        }
        else if (command.startsWith("STEER:")) {
            int targetAngle = command.substring(6).toInt();
            sweepSteering(targetAngle);
            Serial.print("Steering Angle Set to: ");
            Serial.println(targetAngle);
        }
    }
}
