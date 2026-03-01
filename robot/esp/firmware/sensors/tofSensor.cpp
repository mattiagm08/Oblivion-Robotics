#include "TofSensor.h"

bool TofSensor::init() {
    return lox.begin();
}

uint16_t TofSensor::getDistance() {
    VL53L0X_RangingMeasurementData_t measure;
    lox.rangingTest(&measure, false);
    if (measure.RangeStatus != 4) return measure.RangeMilliMeter;
    return 8190; // VALORE MASSIMO INDICANTE ERRORE
}