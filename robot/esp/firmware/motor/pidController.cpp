#include "PIDController.h"

PIDController::PIDController(float kp, float ki, float kd) 
    : _kp(kp), _ki(ki), _kd(kd), _prevError(0), _integral(0) {}

float PIDController::compute(float setpoint, float measured, float dt) {
    float error = setpoint - measured;
    _integral += error * dt;
    float derivative = (error - _prevError) / dt;
    _prevError = error;
    return (_kp * error) + (_ki * _integral) + (_kd * derivative);
}

void PIDController::reset() {
    _prevError = 0;
    _integral = 0;
}