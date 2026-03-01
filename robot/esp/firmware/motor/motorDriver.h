#ifndef MOTOR_DRIVER_H
#define MOTOR_DRIVER_H

#include <Arduino.h>

class MotorDriver {
private:
    int _pinPWM, _pinIN1, _pinIN2;
public:
    MotorDriver(int pwm, int in1, int in2);
    void begin();
    void drive(int speed); // SPEED -255 a 255
    void stop();
};

#endif