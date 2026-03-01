#ifndef IMU_SENSOR_H
#define IMU_SENSOR_H

#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

class IMUSensor {
private:
    Adafruit_MPU6050 mpu;
public:
    bool init();
    float getPitch(); // RITORNA IL PITCH IN GRADI BASATO SULL'ACCELEROMETRO
};

#endif