#ifndef ENCODER_H
#define ENCODER_H

#include <Arduino.h>

class Encoder {
private:
    uint8_t _pinA, _pinB;
    volatile long _count;
public:
    Encoder(uint8_t pinA, uint8_t pinB);
    void init();
    void IRAM_ATTR handleInterrupt();
    long getCount();
    void reset();
};

#endif