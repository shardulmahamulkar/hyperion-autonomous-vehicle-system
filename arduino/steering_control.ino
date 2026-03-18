#include <Servo.h>

#define MOTOR_PIN 9  // PWM pin for motor speed
#define STEERING_PIN 10 // Servo pin for steering

Servo steeringServo;
int motorSpeed = 0;
int steeringAngle = 90; // Default straight position

void setup() {
    Serial.begin(9600);
    steeringServo.attach(STEERING_PIN);
    pinMode(MOTOR_PIN, OUTPUT);
    analogWrite(MOTOR_PIN, motorSpeed); // Start with motor off
    steeringServo.write(steeringAngle); // Center the steering
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
            steeringAngle = command.substring(6).toInt();
            steeringServo.write(steeringAngle);
            Serial.print("Steering Angle Set to: ");
            Serial.println(steeringAngle);
        }
    }
}
