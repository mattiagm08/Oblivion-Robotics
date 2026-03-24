#ifndef MOTOR_DRIVER_H
#define MOTOR_DRIVER_H

#include <Arduino.h>
#include "../config.h"

class MotorDriver {
public:
    void init();
    void setSpeeds(int speedL, int speedR);
    void stop();

private:
    void driveMotor(int pinIn1, int pinIn2, int channel, int speed);
};

#endif