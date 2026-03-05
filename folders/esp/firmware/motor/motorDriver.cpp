#include "motorDriver.h"
#include "../config.h"
#include <Arduino.h>

// ##########################################################################
// INIZIALIZZAZIONE MOTORI                                                  #
// ##########################################################################
void MotorDriver::init() {
    // MOTORE DAVANTI DESTRO
    pinMode(PIN_MOTOR_FR_IN1, OUTPUT);
    pinMode(PIN_MOTOR_FR_IN2, OUTPUT);
    ledcSetup(PWM_CHANNEL_MOTOR_FR, PWM_FREQ, PWM_RESOLUTION);
    ledcAttachPin(PIN_MOTOR_FR_PWM, PWM_CHANNEL_MOTOR_FR);

    // MOTORE DIETRO DESTRO
    pinMode(PIN_MOTOR_BR_IN1, OUTPUT);
    pinMode(PIN_MOTOR_BR_IN2, OUTPUT);
    ledcSetup(PWM_CHANNEL_MOTOR_BR, PWM_FREQ, PWM_RESOLUTION);
    ledcAttachPin(PIN_MOTOR_BR_PWM, PWM_CHANNEL_MOTOR_BR);

    // MOTORE DAVANTI SINISTRO
    pinMode(PIN_MOTOR_FL_IN1, OUTPUT);
    pinMode(PIN_MOTOR_FL_IN2, OUTPUT);
    ledcSetup(PWM_CHANNEL_MOTOR_FL, PWM_FREQ, PWM_RESOLUTION);
    ledcAttachPin(PIN_MOTOR_FL_PWM, PWM_CHANNEL_MOTOR_FL);

    // MOTORE DIETRO SINISTRO
    pinMode(PIN_MOTOR_BL_IN1, OUTPUT);
    pinMode(PIN_MOTOR_BL_IN2, OUTPUT);
    ledcSetup(PWM_CHANNEL_MOTOR_BL, PWM_FREQ, PWM_RESOLUTION);
    ledcAttachPin(PIN_MOTOR_BL_PWM, PWM_CHANNEL_MOTOR_BL);

    stop();
}

// ##########################################################################
// FERMA MOTORI                                                             #
// ##########################################################################
void MotorDriver::stop() {
    // AZZERAMENTO IN/OUT
    digitalWrite(PIN_MOTOR_FR_IN1, LOW);
    digitalWrite(PIN_MOTOR_FR_IN2, LOW);
    digitalWrite(PIN_MOTOR_BR_IN1, LOW);
    digitalWrite(PIN_MOTOR_BR_IN2, LOW);
    digitalWrite(PIN_MOTOR_FL_IN1, LOW);
    digitalWrite(PIN_MOTOR_FL_IN2, LOW);
    digitalWrite(PIN_MOTOR_BL_IN1, LOW);
    digitalWrite(PIN_MOTOR_BL_IN2, LOW);

    // STOP PWM
    ledcWrite(PWM_CHANNEL_MOTOR_FR, 0);
    ledcWrite(PWM_CHANNEL_MOTOR_BR, 0);
    ledcWrite(PWM_CHANNEL_MOTOR_FL, 0);
    ledcWrite(PWM_CHANNEL_MOTOR_BL, 0);
}

// ##########################################################################
// IMPOSTA VELOCITÀ MOTORI                                                  #
// ##########################################################################

// LEFT / RIGHT SPEED: valori da -255 a 255                                  
void MotorDriver::setSpeeds(int leftSpeed, int rightSpeed) {
    // LIMITAZIONE VELOCITÀ
    if (leftSpeed > MOTOR_MAX_PWM) leftSpeed = MOTOR_MAX_PWM;
    if (leftSpeed < -MOTOR_MAX_PWM) leftSpeed = -MOTOR_MAX_PWM;
    if (rightSpeed > MOTOR_MAX_PWM) rightSpeed = MOTOR_MAX_PWM;
    if (rightSpeed < -MOTOR_MAX_PWM) rightSpeed = -MOTOR_MAX_PWM;

    // DEAD BAND
    if (abs(leftSpeed) < MOTOR_DEADBAND) leftSpeed = 0;
    if (abs(rightSpeed) < MOTOR_DEADBAND) rightSpeed = 0;

    // LATO SINISTRO
    if (leftSpeed >= 0) {
        digitalWrite(PIN_MOTOR_FL_IN1, HIGH);
        digitalWrite(PIN_MOTOR_FL_IN2, LOW);
        digitalWrite(PIN_MOTOR_BL_IN1, HIGH);
        digitalWrite(PIN_MOTOR_BL_IN2, LOW);
    } else {
        digitalWrite(PIN_MOTOR_FL_IN1, LOW);
        digitalWrite(PIN_MOTOR_FL_IN2, HIGH);
        digitalWrite(PIN_MOTOR_BL_IN1, LOW);
        digitalWrite(PIN_MOTOR_BL_IN2, HIGH);
        leftSpeed = -leftSpeed;
    }
    ledcWrite(PWM_CHANNEL_MOTOR_FL, leftSpeed);
    ledcWrite(PWM_CHANNEL_MOTOR_BL, leftSpeed);

    // LATO DESTRO
    if (rightSpeed >= 0) {
        digitalWrite(PIN_MOTOR_FR_IN1, HIGH);
        digitalWrite(PIN_MOTOR_FR_IN2, LOW);
        digitalWrite(PIN_MOTOR_BR_IN1, HIGH);
        digitalWrite(PIN_MOTOR_BR_IN2, LOW);
    } else {
        digitalWrite(PIN_MOTOR_FR_IN1, LOW);
        digitalWrite(PIN_MOTOR_FR_IN2, HIGH);
        digitalWrite(PIN_MOTOR_BR_IN1, LOW);
        digitalWrite(PIN_MOTOR_BR_IN2, HIGH);
        rightSpeed = -rightSpeed;
    }
    ledcWrite(PWM_CHANNEL_MOTOR_FR, rightSpeed);
    ledcWrite(PWM_CHANNEL_MOTOR_BR, rightSpeed);
}