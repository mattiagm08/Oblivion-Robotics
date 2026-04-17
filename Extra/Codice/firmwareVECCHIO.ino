// LIBRERIE PER COMUNICAZIONE I2C, SENSORI ToF, IMU E MULTIPLEXER

#include <Wire.h>
#include <Adafruit_VL53L0X.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include "TCA9548.h"

// DEFINIZIONE PIN DRIVER MOTORI 

#define ENA_R 12  
#define IN1_R 14
#define IN2_R 27
#define ENB_R 33 
#define IN3_R 26
#define IN4_R 25 
#define ENA_L 4 
#define IN1_L 16
#define IN2_L 17
#define ENB_L 19  
#define IN3_L 5
#define IN4_L 18

// CONFIGURAZIONE LED ILLUMINAZIONE

#define LED_PIN 32
int ledBrightness = 10;

// CONFIGURAZIONE PIN RESCUE ZONE

#define SILVER_LEFT = 34
#define SILVER_RIGHT = 13
#define GRIPPER = 35

// ISTANZE DEI SENSORI E DEL MULTIPLEXER I2C

TCA9548 i2cMux(0x70);
Adafruit_VL53L0X tofFront = Adafruit_VL53L0X();
Adafruit_VL53L0X tofLeft  = Adafruit_VL53L0X();
Adafruit_VL53L0X tofRight = Adafruit_VL53L0X();
Adafruit_VL53L0X tofBack  = Adafruit_VL53L0X();
Adafruit_MPU6050 mpuSensor;

// VARIABILI GLOBALI PER SENSORI, ORIENTAMENTO E TIMING

float valTFront = 0, valTLeft = 0, valTRight = 0, valTBack = 0;
float gyroZOffset = 0;
float robotHeading = 0;
unsigned long lastMPUTime = 0;
unsigned long lastSensorMillis = 0;
const int sensorInterval = 50;

// COMANDO CORRENTE E VELOCITA' DI ESECUZIONE

String currentCommand = "";
int currentSpeed = 0;

void setup() {

  // INIZIALIZZAZIONE SERIALE 

  Serial.begin(115200);
  Wire.begin(21, 22);
  Wire.setClock(100000);

  // INIZIALIZZAZIONE MOTORI E LED

  initializeMotors();
  stopMotors();
  analogWrite(LED_PIN, ledBrightness);

  // MULTIPLEXER, ToF E GIROSCOPIO

  if (!i2cMux.begin()) Serial.println("MULTIPLEXER ERROR");

  i2cMux.selectChannel(3);
  if (mpuSensor.begin()) {
    mpuSensor.setGyroRange(MPU6050_RANGE_250_DEG);
    mpuSensor.setFilterBandwidth(MPU6050_BAND_21_HZ);
    calibrateMpu();
  }

  initTofSensors();
  lastMPUTime = millis();
}

void loop() {

  // FLOW: READ SERIAL => MPU => MOTORS => ToF => SEND SERIAL 

  readSerial();
  updateMpu();
  moveRobot();
  updateTof();
  sendSerial();
}

// INIZIALIZZAZIONE PIN DEI MOTORI

void initializeMotors() {
  pinMode(ENA_R, OUTPUT); pinMode(IN1_R, OUTPUT); pinMode(IN2_R, OUTPUT);
  pinMode(IN3_R, OUTPUT); pinMode(IN4_R, OUTPUT); pinMode(ENB_R, OUTPUT);
  pinMode(ENA_L, OUTPUT); pinMode(IN1_L, OUTPUT); pinMode(IN2_L, OUTPUT);
  pinMode(IN3_L, OUTPUT); pinMode(IN4_L, OUTPUT); pinMode(ENB_L, OUTPUT);
}

// FUNZIONE PER ARRESTARE TUTTI I MOTORI

void stopMotors() {
  digitalWrite(IN1_R, LOW); digitalWrite(IN2_R, LOW);
  digitalWrite(IN3_R, LOW); digitalWrite(IN4_R, LOW);
  digitalWrite(IN1_L, LOW); digitalWrite(IN2_L, LOW);
  digitalWrite(IN3_L, LOW); digitalWrite(IN4_L, LOW);
  analogWrite(ENA_R, 0); analogWrite(ENB_R, 0);
  analogWrite(ENA_L, 0); analogWrite(ENB_L, 0);
}

// CONTROLLO PWM E DIREZIONE MOTORI DESTRI

void setMotorLeft(int pwm) {
  if (pwm >= 0) {
    digitalWrite(IN1_R, HIGH); digitalWrite(IN2_R, LOW);
    digitalWrite(IN3_R, LOW);  digitalWrite(IN4_R, HIGH);
  } else {
    digitalWrite(IN1_R, LOW);  digitalWrite(IN2_R, HIGH);
    digitalWrite(IN3_R, HIGH); digitalWrite(IN4_R, LOW);
    pwm = -pwm;
  }
  analogWrite(ENA_R, constrain(pwm, 0, 255));
  analogWrite(ENB_R, constrain(pwm, 0, 255));
}

// CONTROLLO PWM E DIREZIONE MOTORI SINISTRI 

void setMotorRight(int pwm) {
  if (pwm >= 0) {
    digitalWrite(IN1_L, LOW);  digitalWrite(IN2_L, HIGH);
    digitalWrite(IN3_L, HIGH); digitalWrite(IN4_L, LOW);
  } else {
    digitalWrite(IN1_L, HIGH); digitalWrite(IN2_L, LOW);
    digitalWrite(IN3_L, LOW);  digitalWrite(IN4_L, HIGH);
    pwm = -pwm;
  }
  analogWrite(ENA_L, constrain(pwm, 0, 255));
  analogWrite(ENB_L, constrain(pwm, 0, 255));
}

// LOGICA DI MOVIMENTO

void moveRobot() {

  // [AVANTI]

  if (currentCommand == "forward") {
    currentSpeed = 200;
    setMotorLeft(currentSpeed);  
    setMotorRight(currentSpeed);
  } 
  
  // [INDIETRO]
  
  else if (currentCommand == "backward") {
    currentSpeed = 150;
    setMotorLeft(-currentSpeed);
    setMotorRight(-currentSpeed);
  } 

  // [SINISTRA]

  else if (currentCommand == "left") {
    currentSpeed = 200;
    setMotorLeft(-currentSpeed);
    setMotorRight(currentSpeed);
  } 
  
  // [DESTRA]

  else if (currentCommand == "right") {
    currentSpeed = 200;
    setMotorLeft(currentSpeed);
    setMotorRight(-currentSpeed);
  } 

  // [INCROCIO SINISTRO]
  
  else if (currentCommand == "leftIntersection") {
      stopMotors();
      delay(1500);
      setMotorLeft(currentSpeed);
      setMotorRight(currentSpeed);
      delay(350); 
      currentSpeed = 200;
      float startHeading = robotHeading;
      while (robotHeading > startHeading - 45) {
          updateMpu();
          setMotorLeft(currentSpeed);
          setMotorRight(-currentSpeed);
      }
      stopMotors();
      currentCommand = "";

  } 

  // [INCROCIO DESTRO]

  else if (currentCommand == "rightIntersection") {
      stopMotors();
      delay(1500);
      setMotorLeft(currentSpeed);
      setMotorRight(currentSpeed);
      delay(350); 
    currentSpeed = 180;
    float startHeading = robotHeading;
    while (robotHeading < startHeading + 45) {
        updateMpu();
        setMotorLeft(-currentSpeed);
        setMotorRight(currentSpeed);
    }
    stopMotors();
    currentCommand = "";
  } 

  // [INVERSIONE]
    
  else if (currentCommand == "turn180") {
      currentSpeed = 200;
      float startHeading = robotHeading;
      while (robotHeading < startHeading + 180) {
          updateMpu();
          setMotorLeft(currentSpeed);
          setMotorRight(-currentSpeed);
      }
      stopMotors();
      currentCommand = "";
  } 

  // [DEFAULT]
  
  else {
    setMotorLeft(0);
    setMotorRight(0);
  }
}

// CALIBRAZIONE DEL GIROSCOPIO (OFFSET ASSE Z)

void calibrateMpu() {
  float sum = 0;
  for (int i = 0; i < 100; i++) {
    sensors_event_t accel, gyro, temp;
    mpuSensor.getEvent(&accel, &gyro, &temp);
    sum += gyro.gyro.z;
    delay(5);
  }
  gyroZOffset = sum / 100.0;
}

// AGGIORNAMENTO DELL'ANGOLO DI ROTAZIONE (HEADING) TRAMITE IMU

float updateMpu() {
  i2cMux.selectChannel(3);
  sensors_event_t accel, gyro, temp;
  mpuSensor.getEvent(&accel, &gyro, &temp);
  unsigned long currentTime = millis();
  float dt = (currentTime - lastMPUTime) / 1000.0;
  lastMPUTime = currentTime;
  float gyroZ = gyro.gyro.z - gyroZOffset;
  if (abs(gyroZ) < 0.03) gyroZ = 0;
  robotHeading += (gyroZ * 180.0 / PI) * dt;
  return robotHeading;
}

// ATTIVAZIONE DEI SENSORI ToF TRAMITE I CANALI DEL MULTIPLEXER

void initTofSensors() {
  i2cMux.selectChannel(5); tofFront.begin();
  i2cMux.selectChannel(7); tofLeft.begin();
  i2cMux.selectChannel(6); tofRight.begin();
  i2cMux.selectChannel(4); tofBack.begin();
}

// LETTURA SEQUENZIALE DEI SENSORI DI DISTANZA ToF

void updateTof() {
  if (millis() - lastSensorMillis < sensorInterval) return;
  lastSensorMillis = millis();
  VL53L0X_RangingMeasurementData_t measure;

  i2cMux.selectChannel(5); tofFront.rangingTest(&measure, false);
  valTFront = (measure.RangeStatus != 4) ? measure.RangeMilliMeter : 999;
  i2cMux.selectChannel(7); tofLeft.rangingTest(&measure, false);
  valTLeft  = (measure.RangeStatus != 4) ? measure.RangeMilliMeter : 999;
  i2cMux.selectChannel(6); tofRight.rangingTest(&measure, false);
  valTRight = (measure.RangeStatus != 4) ? measure.RangeMilliMeter : 999;
  i2cMux.selectChannel(4); tofBack.rangingTest(&measure, false);
  valTBack  = (measure.RangeStatus != 4) ? measure.RangeMilliMeter : 999;
}

// GESTIONE LETTURA SERIALE

void readSerial() {
  // ATTESA DELL'HEADER DI SINCRONIZZAZIONE (0xFF) SEGUITO DAL BYTE COMANDO

  while (Serial.available() >= 2) {
    if (Serial.read() != 0xFF) continue;
    uint8_t cmd = Serial.read();

    switch (cmd) {

      // [START]
      
      case 1:
        currentCommand = "";
        currentSpeed = 0;
        break;

      // [STOP]

      case 2:
        currentCommand = "stop";
        currentSpeed = 0;
        break;
      
      // [AVANTI]
      
      case 3:
        currentCommand = "forward";
        break;
      
      // [INDIETRO]
      
      case 4:
        currentCommand = "backward";
        break;
      
      // [SINISTRA]

      case 5:
        currentCommand = "left";
        break;
      
      // [DESTRA]

      case 6:
        currentCommand = "right";
        break;
      
      // [INCROCIO SINISTRO]

      case 7:
        currentCommand = "leftIntersection";
        break;
      
      // [INCROCIO DESTRO]

      case 8:
        currentCommand = "rightIntersection";
        break;
      
      // [INVERSIONE]

      case 9:
        currentCommand = "turn180";
        break;
      default:
        break;
    }
  }
}

// GESTIONE INVIO SERIALE

void sendSerial() {

  // INVIO HEADER DI SINCRONIZZAZIONE (0xAA) SEGUITO DA 4 UINT16 (ToF) E 1 FLOAT (HEADING)
  // FORMATO LITTLE ENDIAN: <HHHHf = 12 BYTE DI PAYLOAD

  uint8_t payload[13];
  payload[0] = 0xAA;

  uint16_t front = (uint16_t)constrain(valTFront, 0, 65535);
  uint16_t left  = (uint16_t)constrain(valTLeft,  0, 65535);
  uint16_t right = (uint16_t)constrain(valTRight, 0, 65535);
  uint16_t back  = (uint16_t)constrain(valTBack,  0, 65535);

  memcpy(&payload[1],  &front,        sizeof(uint16_t));
  memcpy(&payload[3],  &left,         sizeof(uint16_t));
  memcpy(&payload[5],  &right,        sizeof(uint16_t));
  memcpy(&payload[7],  &back,         sizeof(uint16_t));
  memcpy(&payload[9],  &robotHeading, sizeof(float));

  Serial.write(payload, sizeof(payload));
}