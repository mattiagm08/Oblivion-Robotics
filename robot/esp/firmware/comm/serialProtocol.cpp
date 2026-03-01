#include "serialProtocol.h"
#include "../config.h"

/*
###########################################################################
# COSTRUTTORE                                                             #
###########################################################################
*/
SerialProtocol::SerialProtocol() {
    _buffer.reserve(PKT_MAX_LEN);    // PRE-ALLOCAZIONE BUFFER PACCHETTO
}

/*
###########################################################################
# UPDATE                                                                  #
###########################################################################
# LEGGI SERIAL NON BLOCCANTE                                              #
# RITORNA TRUE SE È STATO COMPLETATO UN NUOVO PACCHETTO                   #
###########################################################################
*/
bool SerialProtocol::update() {
    bool new_data = false;

    while (Serial.available() > 0) {
        char c = Serial.read();

        if (c == PKT_START) {
            _buffer = "";               // INIZIO PACCHETTO
        } else if (c == PKT_END) {
            _parseCommand(_buffer);     // FINE PACCHETTO → PARSING
            _buffer = "";
            new_data = true;
        } else {
            _buffer += c;
            if (_buffer.length() > PKT_MAX_LEN) _buffer = ""; // PROTEZIONE OVERFLOW
        }
    }

    return new_data;
}

/*
###########################################################################
# PARSING COMANDO                                                         #
###########################################################################
# ESTRAPOLA OFFSET E VELOCITÀ DAL PACCHETTO                               #
# FORMATO ATTESO: "off:0.123,spd:150"                                     #
###########################################################################
*/
void SerialProtocol::_parseCommand(String cmd) {
    int offPos = cmd.indexOf("off:");
    int spdPos = cmd.indexOf("spd:");

    if (offPos != -1 && spdPos != -1) {
        int commaPos = cmd.indexOf(PKT_SEP, offPos);
        _offset = cmd.substring(offPos + 4, commaPos).toFloat();
        _speed  = cmd.substring(spdPos + 4).toInt();
    }
}

/*
###########################################################################
# INVIO DATI SENSORI                                                      #
###########################################################################
# INvia DISTANZA, HEADING, PITCH E VALORI ENCODER A RASPBERRY             #
# FORMATO PACCHETTO:                                                      #
# <dist:120,head:45.2,pit:0.1,enL:1000,enR:1005>                          #
###########################################################################
*/
void SerialProtocol::sendSensorData(int dist, float heading, float pitch, long encL, long encR) {
    Serial.print(PKT_START);
    Serial.print("dist:"); Serial.print(dist);
    Serial.print(PKT_SEP);
    Serial.print("head:"); Serial.print(heading, 1);
    Serial.print(PKT_SEP);
    Serial.print("pit:"); Serial.print(pitch, 1);
    Serial.print(PKT_SEP);
    Serial.print("enL:"); Serial.print(encL);
    Serial.print(PKT_SEP);
    Serial.print("enR:"); Serial.print(encR);
    Serial.println(PKT_END);
}