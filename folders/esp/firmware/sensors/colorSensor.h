#ifndef COLOR_SENSOR_H
#define COLOR_SENSOR_H

#include <Arduino.h>
#include <Wire.h>
#include "../config.h"

class ColorSensor {
public:
    void init();
    bool isSilver();
    bool isBlack();

private:
    uint16_t readRawColor();
};

#endif