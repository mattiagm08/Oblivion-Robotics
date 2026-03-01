#ifndef COLOR_SENSOR_H
#define COLOR_SENSOR_H

#include <Adafruit_TCS34725.h>

class ColorSensor {
private:
    Adafruit_TCS34725 tcs;
public:
    bool init();
    void getRGB(float *r, float *g, float *b);
    bool isSilver();
};

#endif