#include "motorDriver.h"
#include <Arduino.h>

void MotorDriver::init() {
    pinMode(PIN_MOTOR_L_IN1, OUTPUT);
    pinMode(PIN_MOTOR_L_IN2, OUTPUT);
    pinMode(PIN_MOTOR_R_IN1, OUTPUT);
    pinMode(PIN_MOTOR_R_IN2, OUTPUT);

    ledcSetup(PWM_CHANNEL_MOTOR_L, PWM_FREQ, PWM_RESOLUTION);
    ledcSetup(PWM_CHANNEL_MOTOR_R, PWM_FREQ, PWM_RESOLUTION);
    
    ledcAttachPin(PIN_MOTOR_L_PWM, PWM_CHANNEL_MOTOR_L);
    ledcAttachPin(PIN_MOTOR_R_PWM, PWM_CHANNEL_MOTOR_R);
}

void MotorDriver::driveMotor(int pinIn1, int pinIn2, int channel, int speed) {
    if (abs(speed) < MOTOR_DEADBAND) speed = 0;
    speed = constrain(speed, -MOTOR_MAX_PWM, MOTOR_MAX_PWM);

    if (speed > 0) {
        digitalWrite(pinIn1, HIGH);
        digitalWrite(pinIn2, LOW);
        ledcWrite(channel, speed);
    } else if (speed < 0) {
        digitalWrite(pinIn1, LOW);
        digitalWrite(pinIn2, HIGH);
        ledcWrite(channel, abs(speed));
    } else {
        digitalWrite(pinIn1, LOW);
        digitalWrite(pinIn2, LOW);
        ledcWrite(channel, 0);
    }
}

void MotorDriver::setSpeeds(int speedL, int speedR) {
    driveMotor(PIN_MOTOR_L_IN1, PIN_MOTOR_L_IN2, PWM_CHANNEL_MOTOR_L, speedL);
    driveMotor(PIN_MOTOR_R_IN1, PIN_MOTOR_R_IN2, PWM_CHANNEL_MOTOR_R, speedR);
}

void MotorDriver::stop() { setSpeeds(0, 0); }