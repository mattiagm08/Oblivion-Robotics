#include "colorSensor.h"
#include <Wire.h>

void ColorSensor::init() {
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
    Wire.beginTransmission(ADDR_COLOR);
    Wire.write(0x00); 
    Wire.write(0x01);
    Wire.endTransmission();
    delay(10);
}

uint16_t ColorSensor::readRawColor() {
    uint16_t value = 0;

    Wire.beginTransmission(ADDR_COLOR);
    Wire.write(0x14);
    Wire.endTransmission(false);
    Wire.requestFrom(ADDR_COLOR, 2, true);

    if (Wire.available() == 2) {
        value = (Wire.read() | (Wire.read() << 8));
    }

    return value;
}

bool ColorSensor::isSilver() {
    uint16_t c = readRawColor();
    return (c > 1500 && c < 3000);
}

bool ColorSensor::isBlack() {
    uint16_t c = readRawColor();
    return (c < 500);
}