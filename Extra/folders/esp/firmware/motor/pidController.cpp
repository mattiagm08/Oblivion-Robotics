#include "PIDController.h"
#include "../config.h"

PIDController::PIDController(float kp, float ki, float kd) 
    : _kp(kp), _ki(ki), _kd(kd), _prevError(0), _integral(0) {}

float PIDController::compute(float setpoint, float measured, float dt) {
    float error = setpoint - measured;

    _integral += error * dt;

    float derivative = (error - _prevError) / dt;
    _prevError = error;

    float output = (_kp * error) + (_ki * _integral) + (_kd * derivative);

    if (output > PID_OUTPUT_MAX) {
        output = PID_OUTPUT_MAX;
        if (_integral > 0) _integral -= error * dt;
    } else if (output < PID_OUTPUT_MIN) {
        output = PID_OUTPUT_MIN;
        if (_integral < 0) _integral -= error * dt;
    }

    return output;
}

void PIDController::reset() {
    _prevError = 0;
    _integral = 0;
}