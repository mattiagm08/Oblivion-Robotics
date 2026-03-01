#include "IMUSensor.h"

bool IMUSensor::init() {
    if (!mpu.begin()) return false;
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    mpu.setGyroRange(MPU6050_RANGE_500_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
    return true;
}

float IMUSensor::getPitch() {
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);
    // CALCOLO DEL PITCH BASATO SULL'ACCELEROMETRO (APPROSSIMAZIONE SEMPLICE)
    return (atan2(a.acceleration.y, a.acceleration.z) * 180.0) / M_PI;
}