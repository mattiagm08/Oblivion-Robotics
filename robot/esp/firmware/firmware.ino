/*
###########################################################################
# FIRMWARE ESP32                                                          #
###########################################################################
*/

#include <Wire.h>
#include <Adafruit_VL53L0X.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include "TCA9548.h"

// PIN MOTORE DESTRO ANTERIORE
#define ENA_D 12  
#define IN1_D 14
#define IN2_D 27

// PIN MOTORE DESTRO POSTERIORE
#define IN3_D 26
#define IN4_D 25
#define ENB_D 33  

// PIN MOTORE SINISTRO POSTERIORE
#define ENA_S 19  
#define IN1_S 18
#define IN2_S 5

// PIN MOTORE SINISTRO ANTERIORE
#define IN3_S 17
#define IN4_S 16
#define ENB_S 4   

// ISTANZA MULTIPLEXER
TCA9548 MP(0x70);

// ISTANZE SENSORI TOF
Adafruit_VL53L0X tf = Adafruit_VL53L0X(); 
Adafruit_VL53L0X ts = Adafruit_VL53L0X(); 
Adafruit_VL53L0X td = Adafruit_VL53L0X(); 

// ISTANZA SENSORE IMU
Adafruit_MPU6050 mpu;

// VARIABILI COMANDO RASPBERRY
float currentOffset = 0.0;
int currentSpeed = 0;

// VARIABILI DATI SENSORI
float valTF = 0, valTS = 0, valTD = 0;
float heading = 0.0; 
long encL = 0, encR = 0;

// VARIABILI CALCOLO ORIENTAMENTO
float gyroZoffset = 0;
unsigned long ultimoTempoMPU = 0;

// VARIABILI TEMPISTICA E CONTROLLO
unsigned long lastSensorMillis = 0;
const int SENSOR_INTERVAL = 50; 
const float K_STEER = 100.0; 
String serialBuffer = "";
bool isReceiving = false;

// INIZIALIZZAZIONE SISTEMA
void setup() {
  // CONFIGURAZIONE SERIALE E I2C
  Serial.begin(115200);
  Wire.begin(21, 22);
  Wire.setClock(100000);

  // CONFIGURAZIONE OUTPUT MOTORI
  inizializeMotors();
  stopMotors();

  // ATTIVAZIONE MULTIPLEXER
  if(!MP.begin()) Serial.println("ERRORE MULTIPLEXER");

  // INIZIALIZZAZIONE MPU6050 SU CANALE 1
  MP.selectChannel(1);
  if (mpu.begin()) {
    mpu.setGyroRange(MPU6050_RANGE_250_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
    calibraMPU();
  }

  // INIZIALIZZAZIONE SENSORI TOF SU CANALI 5, 6, 7
  initToFSensors();

  ultimoTempoMPU = millis();
}

// CICLO PRINCIPALE
void loop() {
  // RICEZIONE COMANDI SERIALI
  leggiSeriale();      
  
  // AGGIORNAMENTO ORIENTAMENTO IMU
  updateMPU();         
  
  // GESTIONE MOVIMENTO MOTORI
  muoviRobot();        
  
  // AGGIORNAMENTO TOF E INVIO DATI
  updateToF();         
}

// INIZIALIZZAZIONE PIN MOTORI
void inizializeMotors() {
  pinMode(ENA_D, OUTPUT); pinMode(IN1_D, OUTPUT); pinMode(IN2_D, OUTPUT);
  pinMode(IN3_D, OUTPUT); pinMode(IN4_D, OUTPUT); pinMode(ENB_D, OUTPUT);
  pinMode(ENA_S, OUTPUT); pinMode(IN1_S, OUTPUT); pinMode(IN2_S, OUTPUT);
  pinMode(IN3_S, OUTPUT); pinMode(IN4_S, OUTPUT); pinMode(ENB_S, OUTPUT);
}

// ARRESTO TOTALE MOTORI
void stopMotors() {
  digitalWrite(IN1_D, LOW); digitalWrite(IN2_D, LOW);
  digitalWrite(IN3_D, LOW); digitalWrite(IN4_D, LOW);
  digitalWrite(IN1_S, LOW); digitalWrite(IN2_S, LOW);
  digitalWrite(IN3_S, LOW); digitalWrite(IN4_S, LOW);
  analogWrite(ENA_D, 0); analogWrite(ENB_D, 0);
  analogWrite(ENA_S, 0); analogWrite(ENB_S, 0);
}

// CALCOLO E APPLICAZIONE POTENZA MOTORI
void muoviRobot() {
  // CONTROLLO ARRESTO DI SICUREZZA
  if (currentSpeed <= 0) { stopMotors(); return; }

  // CALCOLO VELOCITA DIFFERENZIALE
  int baseSpeed = currentSpeed; 
  int correzione = (int)(currentOffset * K_STEER);

  // LIMITAZIONE VALORI PWM
  int speedL = constrain(baseSpeed + correzione, 0, 255);
  int speedR = constrain(baseSpeed - correzione, 0, 255);

  // CONFIGURAZIONE DIREZIONE AVANTI
  digitalWrite(IN1_D, LOW);  digitalWrite(IN2_D, HIGH);
  digitalWrite(IN3_D, HIGH); digitalWrite(IN4_D, LOW);
  digitalWrite(IN1_S, HIGH); digitalWrite(IN2_S, LOW);
  digitalWrite(IN3_S, LOW);  digitalWrite(IN4_S, HIGH);

  // INVIO SEGNALE PWM AI DRIVER
  analogWrite(ENA_D, speedR); analogWrite(ENB_D, speedR);
  analogWrite(ENA_S, speedL); analogWrite(ENB_S, speedL);
}

// CALIBRAZIONE GIROSCOPIO ASSE Z
void calibraMPU() {
  float somma = 0;
  for (int i = 0; i < 100; i++) {
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);
    somma += g.gyro.z;
    delay(5);
  }
  gyroZoffset = somma / 100.0;
}

// INTEGRAZIONE VELOCITA ANGOLARE PER YAW
void updateMPU() {
  MP.selectChannel(1);
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  unsigned long ora = millis();
  float dt = (ora - ultimoTempoMPU) / 1000.0;
  ultimoTempoMPU = ora;

  // FILTRO RUMORE E CALCOLO GRADI
  float gyroZ = g.gyro.z - gyroZoffset;
  if (abs(gyroZ) < 0.03) gyroZ = 0; 

  heading += (gyroZ * 180.0 / PI) * dt;
}

// INIZIALIZZAZIONE SENSORI DISTANZA
void initToFSensors() {
  MP.selectChannel(7); tf.begin();
  MP.selectChannel(6); ts.begin();
  MP.selectChannel(5); td.begin();
}

// LETTURA SENSORI E GESTIONE TEMPISTICA
void updateToF() {
  if (millis() - lastSensorMillis < SENSOR_INTERVAL) return;
  lastSensorMillis = millis();

  VL53L0X_RangingMeasurementData_t measure;

  // LETTURA CANALE FRONTALE
  MP.selectChannel(7); tf.rangingTest(&measure, false);
  valTF = (measure.RangeStatus != 4) ? measure.RangeMilliMeter : 999;

  // LETTURA CANALE SINISTRO
  MP.selectChannel(6); ts.rangingTest(&measure, false);
  valTS = (measure.RangeStatus != 4) ? measure.RangeMilliMeter : 999;

  // LETTURA CANALE DESTRO
  MP.selectChannel(5); td.rangingTest(&measure, false);
  valTD = (measure.RangeStatus != 4) ? measure.RangeMilliMeter : 999;

  // INVIO PACCHETTO DATI SERIALE
  inviaDatiSensori(); 
}

// ANALISI STRINGA RICEVUTA DA RASPBERRY
void leggiSeriale() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '<') { serialBuffer = ""; isReceiving = true; }
    else if (c == '>' && isReceiving) {
      isReceiving = false;
      int offIdx = serialBuffer.indexOf("OFF:");
      int spdIdx = serialBuffer.indexOf("SPD:");
      if (offIdx != -1 && spdIdx != -1) {
        int comma = serialBuffer.indexOf(',', offIdx);
        currentOffset = serialBuffer.substring(offIdx + 4, comma).toFloat();
        currentSpeed = serialBuffer.substring(spdIdx + 4).toInt();
      }
    } else if (isReceiving) { serialBuffer += c; }
  }
}

// TRASMISSIONE DATI FORMATTATI
void inviaDatiSensori() {
  Serial.print("<TF:");   Serial.print(valTF, 1);
  Serial.print(",TS:");   Serial.print(valTS, 1);
  Serial.print(",TD:");   Serial.print(valTD, 1);
  Serial.print(",HEAD:"); Serial.print(heading, 1);
  Serial.print(",ENL:");  Serial.print(encL);
  Serial.print(",ENR:");  Serial.print(encR);
  Serial.println(">");
}