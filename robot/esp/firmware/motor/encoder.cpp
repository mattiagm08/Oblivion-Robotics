#include "Encoder.h"

Encoder::Encoder(uint8_t pinA, uint8_t pinB) : _pinA(pinA), _pinB(pinB), _count(0) {}

void Encoder::init() {
    pinMode(_pinA, INPUT_PULLUP);
    pinMode(_pinB, INPUT_PULLUP);
}

void IRAM_ATTR Encoder::handleInterrupt() {
    if (digitalRead(_pinA) == digitalRead(_pinB)) _count++;
    else _count--;
}

long Encoder::getCount() { return _count; }
void Encoder::reset() { _count = 0; }