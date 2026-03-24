#ifndef IMU_SENSOR_H
#define IMU_SENSOR_H

#include <Arduino.h>
#include <Wire.h>
#include "../config.h"

class IMUSensor {
public:
    void init();
    float getPitch();
    float getHeading();

private:
    float _pitch;
    float _heading;
    void readRawData();
};

#endif