#ifndef SERIAL_PROTOCOL_H
#define SERIAL_PROTOCOL_H

#include <Arduino.h>
#include "../config.h"

class SerialProtocol {
public:
    SerialProtocol();

    bool update();

    float getOffset() const { return _offset; }
    float getSpeed() const { return _speed; }

    void sendSensorData(int dist, float heading, float pitch, long encL, long encR);

private:
    void _parseCommand(const String& cmd);

    String _buffer;
    float _offset;
    float _speed;
};

#endif