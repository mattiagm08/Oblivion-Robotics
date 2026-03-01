#ifndef PID_CONTROLLER_H
#define PID_CONTROLLER_H

class PIDController {
private:
    float _kp, _ki, _kd;
    float _prevError, _integral;
public:
    PIDController(float kp, float ki, float kd);
    float compute(float setpoint, float measured, float dt);
    void reset();
};

#endif