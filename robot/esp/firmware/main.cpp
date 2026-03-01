#include <Arduino.h>
#include "config.h"
#include "motor/motorDriver.h"
#include "motor/pidController.h"
#include "motor/encoder.h"
#include "sensors/imuSensor.h"
#include "sensors/tofSensor.h"
#include "sensors/colorSensor.h"

/*
###########################################################################
# MAIN - ENTRY POINT                                                      #
###########################################################################
# Questo è il file da lanciare sull'ESP 32.                               #
# Gestisce:                                                               #
# - Comunicazione seriale non-bloccante con Raspberry Pi                  #
# - Calcolo correzione sterzata tramite PID                               #
# - Mixaggio motori per movimento differenziale                           #
# - Safety stop se manca aggiornamento dai comandi                        #
# - Telemetria sensori (IMU, ToF, Colore) verso Raspberry                 #
###########################################################################
*/

MotorDriver motors;
PidController linePid(PID_LINE_KP, PID_LINE_KI, PID_LINE_KD, PID_OUTPUT_MIN, PID_OUTPUT_MAX);

// ISTANZE SENSORI E ENCODER
IMUSensor imu;
TofSensor tof;
ColorSensor color;
Encoder encL(PIN_ENCODER_L_A, PIN_ENCODER_L_B);
Encoder encR(PIN_ENCODER_R_A, PIN_ENCODER_R_B);

// VARIABILI DI CONTROLLO
float targetOffset = 0;          // SCOSTAMENTO DELLA LINEA DAL CENTRO
float cruiseSpeed = 0;           // VELOCITÀ BASE DEL ROBOT
unsigned long lastUpdate = 0;    // TIMESTAMP ULTIMO COMANDO RICEVUTO
unsigned long lastTelemetry = 0; // TIMESTAMP INVIO DATI SENSORI

// WRAPPER PER INTERRUPT ENCODER
void IRAM_ATTR handleEncL() { encL.handleInterrupt(); }
void IRAM_ATTR handleEncR() { encR.handleInterrupt(); }

void setup() {
    // INIZIALIZZAZIONE SERIAL
    Serial.begin(SERIAL_BAUD);
    Serial.setTimeout(5); // RIDUCE IL TEMPO DI ATTESA PER IL PARSING

    // GESTIONE HARDWARE PIN XSHUT PER EVITARE CONFLITTO I2C (0x29)
    pinMode(PIN_TOF_XSHUT, OUTPUT);
    digitalWrite(PIN_TOF_XSHUT, LOW); // SPEGNE IL TOF TEMPORANEAMENTE
    delay(10);

    // INIZIALIZZAZIONE MOTORI E ENCODER
    motors.init();
    encL.init();
    encR.init();
    attachInterrupt(digitalPinToInterrupt(PIN_ENCODER_L_A), handleEncL, CHANGE);
    attachInterrupt(digitalPinToInterrupt(PIN_ENCODER_R_A), handleEncR, CHANGE);

    // INIZIALIZZAZIONE SENSORI I2C
    Wire.begin();
    
    // INIZIALIZZA IL COLORE (RESTA SU INDIRIZZO 0x29)
    color.init();

    // RIATTIVA IL TOF E CAMBIA INDIRIZZO A 0x30
    digitalWrite(PIN_TOF_XSHUT, HIGH);
    delay(10);
    tof.init(); 

    imu.init();

    // RESET CONTROLLER PID
    linePid.reset();
}

void loop() {
    // ###########################################################################
    // 1. PARSING SERIALE NON-BLOCCANTE                                          #
    // ###########################################################################
    if (Serial.available() > 0) {
        // CERCA L'INIZIO DEL PACCHETTO
        String data = Serial.readStringUntil('>');
        int startBracket = data.indexOf('<');
        
        if (startBracket != -1) {
            // ESTRAE IL CONTENUTO TRA < E >
            String payload = data.substring(startBracket + 1);
            int offPos = payload.indexOf("off:");
            int spdPos = payload.indexOf("spd:");
            
            if (offPos != -1 && spdPos != -1) {
                // PARSING VALORI TARGET
                targetOffset = payload.substring(offPos + 4, payload.indexOf(',', offPos)).toFloat();
                cruiseSpeed = payload.substring(spdPos + 4).toFloat();
                lastUpdate = millis();
            }
        }
    }

    // ###########################################################################
    // 2. SAFETY CHECK                                                           #
    // ###########################################################################
    if (millis() - lastUpdate > 500) {
        motors.stop();
    } else {
        // ###########################################################################
        // 3. CALCOLO CORREZIONE STERZATA                                            #
        // ###########################################################################
        float steering = linePid.compute(0.0f, targetOffset);

        // ###########################################################################
        // 4. MIXAGGIO MOTORI (DIFFERENZIALE)                                        #
        // ###########################################################################
        int leftPwm = (int)(cruiseSpeed + steering);
        int rightPwm = (int)(cruiseSpeed - steering);

        motors.setSpeeds(leftPwm, rightPwm);
    }

    // ###########################################################################
    // 5. INVIO TELEMETRIA AL RASPBERRY PI (FREQUENZA 20HZ)                       #
    // ###########################################################################
    if (millis() - lastTelemetry > 50) {
        float pitch = imu.getPitch();
        uint16_t dist = tof.getDistance();
        bool silver = color.isSilver();

        // INVIO FORMATTATO PER IL PARSER PYTHON
        Serial.print("D:");
        Serial.print(dist);
        Serial.print(",P:");
        Serial.print(pitch);
        Serial.print(",S:");
        Serial.println(silver ? "1" : "0");

        lastTelemetry = millis();
    }

    // LOOP A 100HZ
    delay(10);
}