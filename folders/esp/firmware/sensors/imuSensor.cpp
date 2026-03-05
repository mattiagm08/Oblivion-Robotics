#include "imuSensor.h"
#include <Wire.h>

void IMUSensor::init() {
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
    Wire.beginTransmission(ADDR_IMU);
    Wire.write(0x6B);
    Wire.write(0);
    Wire.endTransmission(true);
}

void IMUSensor::readRawData() {
    Wire.beginTransmission(ADDR_IMU);
    Wire.write(0x3B);
    Wire.endTransmission(false);
    Wire.requestFrom(ADDR_IMU, 6, true);

    int16_t ax = (Wire.read() << 8) | Wire.read();
    int16_t ay = (Wire.read() << 8) | Wire.read();
    int16_t az = (Wire.read() << 8) | Wire.read();

    _pitch = atan2((float)ax, sqrt((float)ay*(float)ay + (float)az*(float)az)) * 57.2958f;

    Wire.beginTransmission(ADDR_IMU);
    Wire.write(0x43);
    Wire.endTransmission(false);
    Wire.requestFrom(ADDR_IMU, 6, true);

    int16_t gx = (Wire.read() << 8) | Wire.read();
    int16_t gy = (Wire.read() << 8) | Wire.read();
    int16_t gz = (Wire.read() << 8) | Wire.read();

    static float heading = 0;
    static unsigned long lastTime = 0;
    unsigned long now = millis();
    float dt = (lastTime == 0) ? 0.01f : (now - lastTime) / 1000.0f;
    lastTime = now;

    _heading += (float)gz * dt / 131.0f;
}

float IMUSensor::getPitch() {
    readRawData();
    return _pitch;
}

float IMUSensor::getHeading() {
    return _heading;
}