#pragma once
#include <Arduino.h>

/*
###########################################################################
# CLASSE SERIALPROTOCOL                                                   #
###########################################################################
# GESTISCE LA COMUNICAZIONE SERIAL CON LA RASPBERRY                       #
# - RICEZIONE COMANDI                                                     #
# - PARSING PACCHETTI                                                     #
# - INVIO DATI SENSORI                                                    #
###########################################################################
*/
class SerialProtocol {
public:

    /*
    #######################################################################
    # COSTRUTTORE                                                         #
    #######################################################################
    */
    SerialProtocol();
    
    /*
    #######################################################################
    # UPDATE                                                              #
    #######################################################################
    # CONTROLLA SE CI SONO NUOVI DATI SERIAL E LI PROCESSA               #
    # RITORNA TRUE SE È STATO COMPLETATO UN NUOVO PACCHETTO               #
    #######################################################################
    */
    bool update();

    /*
    #######################################################################
    # GETTER                                                               #
    #######################################################################
    # RESTITUISCE I DATI RICEVUTI DALLA RASPBERRY                        #
    #######################################################################
    */
    float getTargetOffset() const { return _offset; }
    int getTargetSpeed() const { return _speed; }

    /*
    #######################################################################
    # INVIO DATI SENSORI                                                   #
    #######################################################################
    # INvia DISTANZA, HEADING, PITCH E VALORI ENCODER A RASPBERRY         #
    #######################################################################
    */
    void sendSensorData(int dist, float heading, float pitch, long encL, long encR);

private:
    float _offset = 0.0f;      // OFFSET LINEA
    int _speed = 0;             // VELOCITÀ TARGET
    String _buffer = "";        // BUFFER PACCHETTO
    
    /*
    #######################################################################
    # PARSING COMANDO                                                      #
    #######################################################################
    # ESTRAPOLA OFFSET E VELOCITÀ DAL PACCHETTO                           #
    #######################################################################
    */
    void _parseCommand(String cmd);
};