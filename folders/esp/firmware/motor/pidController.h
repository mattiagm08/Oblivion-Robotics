#include "pidController.h"

PidController::PidController(float kp, float ki, float kd, float outMin, float outMax, float integralLimit)
    : _kp(kp), _ki(ki), _kd(kd),
      _outMin(outMin), _outMax(outMax),
      _integralLimit(integralLimit),
      _prevError(0), _integral(0),
      _prevDerivative(0), _lastTime(0) {}

float PidController::compute(float setpoint, float measured) {

    unsigned long now = millis();
    float dt = (_lastTime == 0) ? 0.01f : (now - _lastTime) / 1000.0f;
    _lastTime = now;

    if (dt <= 0.0001f) dt = 0.0001f;

    float error = setpoint - measured;

    _integral += error * dt;

    if (_integral > _integralLimit) _integral = _integralLimit;
    if (_integral < -_integralLimit) _integral = -_integralLimit;

    float derivativeRaw = (error - _prevError) / dt;
    float derivative = 0.7f * _prevDerivative + 0.3f * derivativeRaw;

    _prevDerivative = derivative;
    _prevError = error;

    float output = (_kp * error) + (_ki * _integral) + (_kd * derivative);

    if (output > _outMax) output = _outMax;
    if (output < _outMin) output = _outMin;

    return output;
}

void PidController::reset() {
    _prevError = 0;
    _integral = 0;
    _prevDerivative = 0;
    _lastTime = 0;
}