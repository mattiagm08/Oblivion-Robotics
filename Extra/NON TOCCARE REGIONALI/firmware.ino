#include <Wire.h>
#include <Adafruit_VL53L0X.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include "TCA9548.h"

#define ENA_D 12  
#define IN1_D 14
#define IN2_D 27
#define ENB_D 33 
#define IN3_D 26
#define IN4_D 25 
#define ENA_S 4 
#define IN1_S 16
#define IN2_S 17
#define ENB_S 19  
#define IN3_S 5
#define IN4_S 18

// CONFIGURAZIONE LED ILLUMINAZIONE

#define LED_PIN 32
int ledBrightness = 10;

TCA9548 MP(0x70);
Adafruit_VL53L0X tf = Adafruit_VL53L0X();
Adafruit_VL53L0X ts = Adafruit_VL53L0X();
Adafruit_VL53L0X td = Adafruit_VL53L0X();
Adafruit_MPU6050 mpu;

float valTF = 0, valTS = 0, valTD = 0;
float gyroZoffset = 0;
float heading = 0;
unsigned long ultimoTempoMPU = 0;
unsigned long lastSensorMillis = 0;

const int SENSOR_INTERVAL = 50;

String serialBuffer = "";

String comandoAttuale = "";
int velocitaAttuale = 0;

void setup(){
  Serial.begin(115200);
  Wire.begin(21, 22);
  Wire.setClock(100000);
  inizializeMotors();
  stopMotors();
  analogWrite(LED_PIN, ledBrightness);


  if (!MP.begin()) Serial.println("ERRORE MULTIPLEXER");

  MP.selectChannel(3);
  if (mpu.begin()) {
    mpu.setGyroRange(MPU6050_RANGE_250_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
    calibraMPU();
  }

  initToFSensors();
  ultimoTempoMPU = millis();
}

void loop(){
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

void setMotorRight(int pwm) {
  if (pwm >= 0) {
    digitalWrite(IN1_D, LOW);  digitalWrite(IN2_D, HIGH);
    digitalWrite(IN3_D, HIGH); digitalWrite(IN4_D, LOW);
  } else {
    digitalWrite(IN1_D, HIGH); digitalWrite(IN2_D, LOW);
    digitalWrite(IN3_D, LOW);  digitalWrite(IN4_D, HIGH);
    pwm = -pwm;
  }
  analogWrite(ENA_D, constrain(pwm, 0, 255));
  analogWrite(ENB_D, constrain(pwm, 0, 255));
}

void setMotorLeft(int pwm) {
  if (pwm >= 0) {
    digitalWrite(IN1_S, HIGH); digitalWrite(IN2_S, LOW);
    digitalWrite(IN3_S, LOW);  digitalWrite(IN4_S, HIGH);
  } else {
    digitalWrite(IN1_S, LOW);  digitalWrite(IN2_S, HIGH);
    digitalWrite(IN3_S, HIGH); digitalWrite(IN4_S, LOW);
    pwm = -pwm;
  }
  analogWrite(ENA_S, constrain(pwm, 0, 255));
  analogWrite(ENB_S, constrain(pwm, 0, 255));
}

void muoviRobot(){
  if (comandoAttuale == "avanti") {
    velocitaAttuale = 200;
    setMotorLeft(-velocitaAttuale);
    setMotorRight(-velocitaAttuale);
  } else if (comandoAttuale == "indietro") {
    velocitaAttuale = 150;
    setMotorLeft(velocitaAttuale);
    setMotorRight(velocitaAttuale);
  } else if (comandoAttuale == "destra") {
    velocitaAttuale = 200;
    setMotorLeft(velocitaAttuale);
    setMotorRight(-velocitaAttuale*1.1);
  } else if (comandoAttuale == "sinistra") {
    velocitaAttuale = 200;
    setMotorLeft(-velocitaAttuale*1.1);
    setMotorRight(velocitaAttuale);
  } else if (comandoAttuale == "incrociodx") {
      stopMotors();
      delay(1500);
      setMotorLeft(-velocitaAttuale);
      setMotorRight(-velocitaAttuale);
      delay(350); 
    velocitaAttuale = 180;
    float heading_start = heading;
    while (heading < heading_start + 45) {
        updateMPU();
        setMotorLeft(velocitaAttuale);
        setMotorRight(-velocitaAttuale);
    }
    stopMotors();
    comandoAttuale = "";

  } else if (comandoAttuale == "incrociosx") {
      stopMotors();
      delay(1500);
      setMotorLeft(-velocitaAttuale);
      setMotorRight(-velocitaAttuale);
      delay(350); 
      velocitaAttuale = 200;
      float heading_start = heading;
      while (heading > heading_start - 45) {
          updateMPU();
          setMotorLeft(velocitaAttuale);
          setMotorRight(-velocitaAttuale);
      }
      stopMotors();
      comandoAttuale = "";

  } else if (comandoAttuale == "inversione") {
      velocitaAttuale = 200;
      float heading_start = heading;
      while (heading < heading_start + 180) {
          updateMPU();
          setMotorLeft(-velocitaAttuale);
          setMotorRight(velocitaAttuale);
      }
      stopMotors();
      comandoAttuale = "";
  } else {
    setMotorLeft(0);
    setMotorRight(0);
  }
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

float updateMPU() {
  MP.selectChannel(3);
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  unsigned long ora = millis();
  float dt = (ora - ultimoTempoMPU) / 1000.0;
  ultimoTempoMPU = ora;
  float gyroZ = g.gyro.z - gyroZoffset;
  if (abs(gyroZ) < 0.03) gyroZ = 0;
  heading += (gyroZ * 180.0 / PI) * dt;
  return heading;
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

}

void leggiSeriale(){
  while(Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      serialBuffer.trim();
      if (serialBuffer.length() > 0) {
        int sep = serialBuffer.indexOf(':');
        if (sep != -1) {
          comandoAttuale = serialBuffer.substring(0, sep);
          velocitaAttuale = serialBuffer.substring(sep + 1).toInt();
        } else if (serialBuffer == "stop") {
          comandoAttuale = "stop";
          velocitaAttuale = 0;
        } else if (serialBuffer == "START") {
          comandoAttuale = "";
          velocitaAttuale = 0;
        } else {
          comandoAttuale = serialBuffer;
          velocitaAttuale = 100;
        }
      }
      serialBuffer = "";
    } else {
      serialBuffer += c;
    }
  }
}
