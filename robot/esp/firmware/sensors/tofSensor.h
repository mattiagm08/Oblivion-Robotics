#ifndef TOF_SENSOR_H
#define TOF_SENSOR_H

#include <Adafruit_VL53L0X.h>

class TofSensor {
private:
    Adafruit_VL53L0X lox;
public:
    bool init();
    uint16_t getDistance(); // DISTANZA IN MM
};

#endif