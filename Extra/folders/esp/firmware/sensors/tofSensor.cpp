#include "tofSensor.h"
#include <Wire.h>

void TofSensor::init() {

    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);

    pinMode(PIN_TOF_XSHUT, OUTPUT);
    digitalWrite(PIN_TOF_XSHUT, HIGH);
    delay(10);

    Wire.beginTransmission(ADDR_TOF_NEW);
    Wire.write(0x00);
    Wire.endTransmission();
}

uint16_t TofSensor::getDistance() {
    _distance = 0;

    Wire.beginTransmission(ADDR_TOF_NEW);
    Wire.write(0x01);
    Wire.endTransmission(false);
    Wire.requestFrom(ADDR_TOF_NEW, 2, true);

    if (Wire.available() == 2) {
        _distance = (Wire.read() << 8) | Wire.read();
    }

    return _distance;
}