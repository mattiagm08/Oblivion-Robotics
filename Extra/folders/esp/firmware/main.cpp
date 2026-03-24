#include <Arduino.h>
#include "config.h"
#include "motor/motorDriver.h"
#include "motor/pidController.h"
#include "motor/encoder.h"
#include "sensors/imuSensor.h"
#include "sensors/tofSensor.h"
#include "sensors/colorSensor.h"
#include "comm/serialProtocol.h"
#include "actuators/rescueArm.h"

// ##########################################################################
// ISTANZE GLOBALI DEL ROBOT                                               #
// ##########################################################################
// Motori, sensori, PID, encoder, comunicazione seriale                    #
// ##########################################################################

MotorDriver motors;
PidController linePid(PID_LINE_KP, PID_LINE_KI, PID_LINE_KD, PID_OUTPUT_MIN, PID_OUTPUT_MAX);

IMUSensor imu;
TofSensor tof;
ColorSensor color;
RescueArm arm(PIN_ARM_SERVO);

Encoder encL(PIN_ENCODER_L_A, PIN_ENCODER_L_B);
Encoder encR(PIN_ENCODER_R_A, PIN_ENCODER_R_B);

SerialProtocol serial;

// ##########################################################################
// VARIABILI DI CONTROLLO E TELEMETRIA                                      #
// ##########################################################################

float targetOffset = 0.0f;
int cruiseSpeed = 0;
unsigned long lastUpdate = 0;
unsigned long lastTelemetry = 0;
unsigned long prevLoopTime = 0;

// ##########################################################################
// INTERRUPT HANDLER ENCODER                                               #
// ##########################################################################

void IRAM_ATTR handleEncL() { encL.handleInterrupt(); }
void IRAM_ATTR handleEncR() { encR.handleInterrupt(); }

// ##########################################################################
// SETUP - Inizializzazione completa del robot                             #
// ##########################################################################

void setup() {
    Serial.begin(SERIAL_BAUD);
    Serial.setTimeout(5);
    DEBUG_PRINTLN("\\n\\n[SETUP] Starting...");

    // Configura pin XSHUT del TOF (deve stare basso per escluderlo inizialmente)
    pinMode(PIN_TOF_XSHUT, OUTPUT);
    digitalWrite(PIN_TOF_XSHUT, LOW);
    delay(10);

    // Init I2C PRIMA dei sensori
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
    delay(100);

    // Init motori
    motors.init();
    DEBUG_PRINTLN("[SETUP] Motors initialized");

    // Init encoder
    encL.init();
    encR.init();
    attachInterrupt(digitalPinToInterrupt(PIN_ENCODER_L_A), handleEncL, CHANGE);
    attachInterrupt(digitalPinToInterrupt(PIN_ENCODER_R_A), handleEncR, CHANGE);
    DEBUG_PRINTLN("[SETUP] Encoders initialized");

    // Init sensori colore
    color.init();
    DEBUG_PRINTLN("[SETUP] Color sensor initialized");

    // Abilita TOF
    digitalWrite(PIN_TOF_XSHUT, HIGH);
    delay(50);
    tof.init();
    DEBUG_PRINTLN("[SETUP] ToF sensor initialized");

    // Init IMU
    imu.init();
    DEBUG_PRINTLN("[SETUP] IMU initialized");

    // Init braccio rescue
    arm.init();
    DEBUG_PRINTLN("[SETUP] Rescue arm initialized");

    // Reset PID
    linePid.reset();
    prevLoopTime = millis();
    lastUpdate = millis();
    lastTelemetry = millis();

    DEBUG_PRINTLN("[SETUP] Complete! Ready to roll.\\n");
}

// ##########################################################################
// LOOP PRINCIPALE                                                          #
// ##########################################################################
// 1. Calcolo dt loop per PID                                               #
// 2. Lettura dati seriali non bloccante                                    #
// 3. Controllo safety stop                                                 #
// 4. Calcolo correzione sterzata PID                                       #
// 5. Mixaggio motori differenziali                                         #
// 6. Invio telemetria sensori a Raspberry Pi                               #
// ##########################################################################

void loop() {
    unsigned long now = millis();
    float dt = (now - prevLoopTime) / 1000.0f;
    if (dt <= 0) dt = 0.001f;
    prevLoopTime = now;

    // ########################################################################
    // LETTURA COMANDI SERIALI                                                #
    // ########################################################################
    if (serial.update()) {
        targetOffset = serial.getOffset();
        cruiseSpeed = serial.getSpeed();
        lastUpdate = millis();
        DEBUG_PRINT("[RX] OFF:");
        DEBUG_PRINT(targetOffset);
        DEBUG_PRINT(" SPD:");
        DEBUG_PRINTLN(cruiseSpeed);
    }

    // ########################################################################
    // SAFETY STOP - Se perdi comunicazione, ferma tutto                      #
    // ########################################################################
    if (millis() - lastUpdate > SERIAL_WATCHDOG_MS) {
        motors.stop();
        if (millis() - lastUpdate == SERIAL_WATCHDOG_MS + 1) {
            DEBUG_PRINTLN("[SAFETY] Watchdog timeout - motors stopped");
        }
    } else {
        // ####################################################################
        // CALCOLO CONTROLLO STERZATA CON PID                                 #
        // ####################################################################
        float steering = linePid.compute(0.0f, targetOffset, dt);

        int leftPwm  = (int)(cruiseSpeed + steering);
        int rightPwm = (int)(cruiseSpeed - steering);

        // ####################################################################
        // SETTAGGIO VELOCITÀ MOTORI                                         #
        // ####################################################################
        motors.setSpeeds(leftPwm, rightPwm);
    }

    // ########################################################################
    // TELEMETRIA SENSORI                                                     #
    // ########################################################################
    if (millis() - lastTelemetry >= TELEMETRY_PERIOD_MS) {
        float pitch   = imu.getPitch();
        float heading = imu.getHeading();
        uint16_t dist = tof.getDistance();
        
        long encLCount = encL.getCount();
        long encRCount = encR.getCount();

        serial.sendSensorData(dist, heading, pitch, encLCount, encRCount);
        lastTelemetry = millis();
    }

    // ########################################################################
    // GESTIONE BRACCIO RESCUE                                                #
    // ########################################################################
    if (arm.isPressed()) {
        arm.open();
        delay(500);  // Debouncing
    }

    delay(LOOP_PERIOD_MS);
}