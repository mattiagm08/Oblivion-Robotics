#include "ColorSensor.h"

bool ColorSensor::init() {
    return tcs.begin();
}

void ColorSensor::getRGB(float *r, float *g, float *b) {
    tcs.getRGB(r, g, b);
}

bool ColorSensor::isSilver() {
    float r, g, b;
    tcs.getRGB(&r, &g, &b);
    // SEMPLICE LOGICA PER RILEVARE IL COLORE ARGENTO BASATA SU SOGLIE DI LUMINOSITÀ E SIMILITUDINE TRA I CANALI
    return (r > 180 && g > 180 && b > 180 && abs(r-g) < 20);
}