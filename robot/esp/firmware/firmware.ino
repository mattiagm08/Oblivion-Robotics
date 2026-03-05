#include <Wire.h>
#include <Adafruit_VL53L0X.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include "TCA9548.h"

#define ENA_D 12  
#define IN1_D 14
#define IN2_D 27
#define IN3_D 26
#define IN4_D 25
#define ENB_D 33  
#define ENA_S 19  
#define IN1_S 18
#define IN2_S 5
#define IN3_S 17
#define IN4_S 16
#define ENB_S 4  

TCA9548 MP(0x70);
Adafruit_VL53L0X tf = Adafruit_VL53L0X();
Adafruit_VL53L0X ts = Adafruit_VL53L0X();
Adafruit_VL53L0X td = Adafruit_VL53L0X();
Adafruit_MPU6050 mpu;

float currentOffset = 0.0;
int currentSpeed = 0;
float valTF = 0, valTS = 0, valTD = 0;
float heading = 0.0;
long encL = 0, encR = 0;
float gyroZoffset = 0;
unsigned long ultimoTempoMPU = 0;
unsigned long lastSensorMillis = 0;
const int SENSOR_INTERVAL = 50;
const float K_STEER = 100.0;
String serialBuffer = "";
bool isReceiving = false;

// Velocità base per la rotazione sul posto (regola questo valore, da 0 a 255)
const int TURN_SPEED = 180; 

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);
  Wire.setClock(100000);
  inizializeMotors();
  stopMotors();
  if (!MP.begin()) Serial.println("ERRORE MULTIPLEXER");
  MP.selectChannel(1);
  if (mpu.begin()) {
    mpu.setGyroRange(MPU6050_RANGE_250_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
    calibraMPU();
  }
  initToFSensors();
  ultimoTempoMPU = millis();
}

void loop() {
  leggiSeriale();
  updateMPU();
  muoviRobot();
  updateToF();
}

void inizializeMotors() {
  pinMode(ENA_D, OUTPUT); pinMode(IN1_D, OUTPUT); pinMode(IN2_D, OUTPUT);
  pinMode(IN3_D, OUTPUT); pinMode(IN4_D, OUTPUT); pinMode(ENB_D, OUTPUT);
  pinMode(ENA_S, OUTPUT); pinMode(IN1_S, OUTPUT); pinMode(IN2_S, OUTPUT);
  pinMode(IN3_S, OUTPUT); pinMode(IN4_S, OUTPUT); pinMode(ENB_S, OUTPUT);
}

void stopMotors() {
  digitalWrite(IN1_D, LOW); digitalWrite(IN2_D, LOW);
  digitalWrite(IN3_D, LOW); digitalWrite(IN4_D, LOW);
  digitalWrite(IN1_S, LOW); digitalWrite(IN2_S, LOW);
  digitalWrite(IN3_S, LOW); digitalWrite(IN4_S, LOW);
  analogWrite(ENA_D, 0); analogWrite(ENB_D, 0);
  analogWrite(ENA_S, 0); analogWrite(ENB_S, 0);
}

void setMotorLeft(int pwm) {
  if (pwm >= 0) {
    digitalWrite(IN1_S, HIGH); digitalWrite(IN2_S, LOW);
    digitalWrite(IN3_S, LOW); digitalWrite(IN4_S, HIGH);
  } else {
    digitalWrite(IN1_S, LOW); digitalWrite(IN2_S, HIGH);
    digitalWrite(IN3_S, HIGH); digitalWrite(IN4_S, LOW);
    pwm = -pwm;
  }
  analogWrite(ENA_S, pwm);
  analogWrite(ENB_S, pwm);
}

void setMotorRight(int pwm) {
  if (pwm >= 0) {
    digitalWrite(IN1_D, LOW); digitalWrite(IN2_D, HIGH);
    digitalWrite(IN3_D, HIGH); digitalWrite(IN4_D, LOW);
  } else {
    digitalWrite(IN1_D, HIGH); digitalWrite(IN2_D, LOW);
    digitalWrite(IN3_D, LOW); digitalWrite(IN4_D, HIGH);
    pwm = -pwm;
  }
  analogWrite(ENA_D, pwm);
  analogWrite(ENB_D, pwm);
}

void muoviRobot() {
  if (currentSpeed == 0) { stopMotors(); return; }
  
  int correzione = (int)(currentOffset * K_STEER);
  int speedL = 0;
  int speedR = 0;

  if (correzione > 7) { 
    // Curva a destra stretta: sinistra avanti veloce, destra indietro veloce
    speedL = TURN_SPEED + abs(correzione / 2); // Aumenta con l'errore
    speedR = -speedL/2;
  } 
  else if (correzione < -7) { 
    // Curva a sinistra stretta: destra avanti veloce, sinistra indietro veloce
    speedR = TURN_SPEED + abs(correzione / 2); // Aumenta con l'errore
    speedL = -speedR/2;
  } 
  else {
    // Andamento normale dritto o correzioni minime
    speedL = constrain(currentSpeed + correzione, -255, 255);
    speedR = constrain(currentSpeed - correzione, -255, 255);
  }

  // Sicurezza finale sui limiti PWM
  speedL = constrain(speedL, -255, 255);
  speedR = constrain(speedR, -255, 255);

  setMotorLeft(speedL);
  setMotorRight(speedR);
}

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

void updateMPU() {
  MP.selectChannel(1);
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  unsigned long ora = millis();
  float dt = (ora - ultimoTempoMPU) / 1000.0;
  ultimoTempoMPU = ora;
  float gyroZ = g.gyro.z - gyroZoffset;
  if (abs(gyroZ) < 0.03) gyroZ = 0;
  heading += (gyroZ * 180.0 / PI) * dt;
}

void initToFSensors() {
  MP.selectChannel(7); tf.begin();
  MP.selectChannel(6); ts.begin();
  MP.selectChannel(5); td.begin();
}

void updateToF() {
  if (millis() - lastSensorMillis < SENSOR_INTERVAL) return;
  lastSensorMillis = millis();
  VL53L0X_RangingMeasurementData_t measure;
  MP.selectChannel(7); tf.rangingTest(&measure, false);
  valTF = (measure.RangeStatus != 4) ? measure.RangeMilliMeter : 999;
  MP.selectChannel(6); ts.rangingTest(&measure, false);
  valTS = (measure.RangeStatus != 4) ? measure.RangeMilliMeter : 999;
  MP.selectChannel(5); td.rangingTest(&measure, false);
  valTD = (measure.RangeStatus != 4) ? measure.RangeMilliMeter : 999;
  inviaDatiSensori();
}

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
        currentSpeed  = serialBuffer.substring(spdIdx + 4).toInt();
      }
    } else if (isReceiving) { serialBuffer += c; }
  }
}

void inviaDatiSensori() {
  Serial.print("<TF:"); Serial.print(valTF, 1);
  Serial.print(",TS:"); Serial.print(valTS, 1);
  Serial.print(",TD:"); Serial.print(valTD, 1);
  Serial.print(",HEAD:"); Serial.print(heading, 1);
  Serial.print(",ENL:"); Serial.print(encL);
  Serial.print(",ENR:"); Serial.print(encR);
  Serial.println(">");
}