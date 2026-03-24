#ifndef ENCODER_H
#define ENCODER_H

#include <Arduino.h>

class Encoder {
public:
    Encoder(uint8_t pinA, uint8_t pinB);

    void init();
    void reset();
    long getCount();
    void IRAM_ATTR handleInterrupt();

private:
    uint8_t _pinA;
    uint8_t _pinB;
    volatile long _count;
};

#endif