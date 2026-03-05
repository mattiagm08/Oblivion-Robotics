#include "serialProtocol.h"
#include "../config.h"

SerialProtocol::SerialProtocol() : _offset(0), _speed(0) {
    _buffer.reserve(PKT_MAX_LEN);
}

bool SerialProtocol::update() {
    bool new_data = false;

    while (Serial.available() > 0) {
        char c = Serial.read();

        if (c == PKT_START) {
            _buffer = "";
        } else if (c == PKT_END) {
            _parseCommand(_buffer);
            _buffer = "";
            new_data = true;
        } else {
            _buffer += c;
            if (_buffer.length() > PKT_MAX_LEN) _buffer = "";
        }
    }

    return new_data;
}

void SerialProtocol::_parseCommand(String cmd) {

    int offPos = cmd.indexOf("OFF:");
    int spdPos = cmd.indexOf("SPD:");

    if (offPos != -1 && spdPos != -1) {

        int commaPos = cmd.indexOf(PKT_SEP, offPos);

        _offset = cmd.substring(offPos + 4, commaPos).toFloat();
        _speed  = cmd.substring(spdPos + 4).toInt();
    }
}

float SerialProtocol::getOffset() const {
    return _offset;
}

int SerialProtocol::getSpeed() const {
    return _speed;
}

void SerialProtocol::sendSensorData(int dist, float heading, float pitch, long encL, long encR) {

    Serial.print(PKT_START);

    Serial.print("DIST:"); Serial.print(dist);
    Serial.print(PKT_SEP);

    Serial.print("HEAD:"); Serial.print(heading, 1);
    Serial.print(PKT_SEP);

    Serial.print("PIT:"); Serial.print(pitch, 1);
    Serial.print(PKT_SEP);

    Serial.print("ENL:"); Serial.print(0);
    Serial.print(PKT_SEP);

    Serial.print("ENR:"); Serial.print(0);

    Serial.println(PKT_END);
}