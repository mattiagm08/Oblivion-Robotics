#ifndef TOF_SENSOR_H
#define TOF_SENSOR_H

#include <Arduino.h>
#include <Wire.h>
#include "../config.h"

class TofSensor {
public:
    void init();
    uint16_t getDistance();

private:
    uint16_t _distance;
};

#endif