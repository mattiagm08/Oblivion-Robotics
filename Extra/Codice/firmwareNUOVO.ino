// LIBRERIE PER COMUNICAZIONE I2C, SENSORI ToF, IMU E MULTIPLEXER

#include <Wire.h>
#include <Adafruit_VL53L0X.h>
#include <Adafruit_BNO055.h>
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

#define SILVER_LEFT 34
#define SILVER_RIGHT 13
#define GRIPPER 35

#define PID_STRAIGHT_KP  2.5  
#define PID_STRAIGHT_KI  0.002
#define PID_STRAIGHT_KD  0.45 

// GUADAGNI PID ROTAZIONE (INCROCI E INVERSIONE)

#define PID_TURN_KP       4.5
#define PID_TURN_KI       0.0
#define PID_TURN_KD       0.8 

// SOGLIA DI ARRESTO ROTAZIONE IN GRADI

#define PID_TURN_THRESHOLD   3.0
#define PID_TURN_MIN_SPEED   80
#define PID_TURN_MAX_SPEED   125 

// ISTANZE DEI SENSORI E DEL MULTIPLEXER I2C

TCA9548 i2cMux(0x70);
Adafruit_VL53L0X tofFront = Adafruit_VL53L0X();
Adafruit_VL53L0X tofLeft  = Adafruit_VL53L0X();
Adafruit_VL53L0X tofRight = Adafruit_VL53L0X();
Adafruit_VL53L0X tofBack  = Adafruit_VL53L0X();
Adafruit_BNO055 mpuSensor = Adafruit_BNO055(55, 0x29);

// VARIABILI GLOBALI

float valTFront = 0, valTLeft = 0, valTRight = 0, valTBack = 0;
float headingOffset = 0;
float robotHeading = 0;
unsigned long lastMPUTime = 0;
unsigned long lastSensorMillis = 0;
const int sensorInterval = 50;

bool imuReady = false;
bool imuStable = false;

// VARIABILI DI STATO PID

float pidIntegral  = 0;
float pidPrevError = 0;
float pidSetpoint  = 0;
unsigned long pidLastTime = 0;

String currentCommand = "";
int    currentSpeed   = 0;
float  currentOffset  = 0;

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);
  Wire.setClock(100000);

  initializeMotors();
  stopMotors();
  analogWrite(LED_PIN, ledBrightness);

  if (!i2cMux.begin()) Serial.println("MULTIPLEXER ERROR");

  i2cMux.selectChannel(3);
  imuReady = mpuSensor.begin();
  if (!imuReady) {
    Serial.println("BNO055 NOT FOUND");
  } else {
    delay(500);
    mpuSensor.setExtCrystalUse(true);
    resetHeading();
    imuStable = true;
  }

  initTofSensors();
  lastMPUTime = millis();
}

void loop() {
  readSerial();
  updateMpu();
  moveRobot();
  updateTof();
  sendSerial();
}

void initializeMotors() {
  pinMode(ENA_R, OUTPUT); pinMode(IN1_R, OUTPUT); pinMode(IN2_R, OUTPUT);
  pinMode(IN3_R, OUTPUT); pinMode(IN4_R, OUTPUT); pinMode(ENB_R, OUTPUT);
  pinMode(ENA_L, OUTPUT); pinMode(IN1_L, OUTPUT); pinMode(IN2_L, OUTPUT);
  pinMode(IN3_L, OUTPUT); pinMode(IN4_L, OUTPUT); pinMode(ENB_L, OUTPUT);
}

void stopMotors() {
  digitalWrite(IN1_R, LOW); digitalWrite(IN2_R, LOW);
  digitalWrite(IN3_R, LOW); digitalWrite(IN4_R, LOW);
  digitalWrite(IN1_L, LOW); digitalWrite(IN2_L, LOW);
  digitalWrite(IN3_L, LOW); digitalWrite(IN4_L, LOW);
  analogWrite(ENA_R, 0); analogWrite(ENB_R, 0);
  analogWrite(ENA_L, 0); analogWrite(ENB_L, 0);
}

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

void resetPid(float setpoint) {
  pidSetpoint  = setpoint;
  pidIntegral  = 0;
  pidPrevError = 0;
  pidLastTime  = millis();
}

float computePid(float setpoint, float input, float kp, float ki, float kd) {
  unsigned long now = millis();
  float dt = (now - pidLastTime) / 1000.0;
  pidLastTime = now;
  if (dt <= 0 || dt > 0.2) dt = 0.02;
  float error      = setpoint - input;
  pidIntegral     += error * dt;
  pidIntegral      = constrain(pidIntegral, -50, 50);
  float derivative = (error - pidPrevError) / dt;
  pidPrevError     = error;
  return (kp * error) + (ki * pidIntegral) + (kd * derivative);
}

void moveRobot() {
  static String prevCommand = "";

  if (currentCommand != prevCommand) {
    resetPid(robotHeading);
    prevCommand = currentCommand;
  }

  if (currentCommand == "drive") {
    currentSpeed = 125;
    float correction = computePid(0, currentOffset, PID_STRAIGHT_KP, PID_STRAIGHT_KI, PID_STRAIGHT_KD);
    
    int adaptiveSpeed = currentSpeed;
    if (abs(currentOffset) > 150) adaptiveSpeed = 100; 

    setMotorLeft(adaptiveSpeed - (int)correction);
    setMotorRight(adaptiveSpeed + (int)correction);
  } 
  else if (currentCommand == "backward") {
    currentSpeed = 125;
    float correction = computePid(pidSetpoint, robotHeading, PID_STRAIGHT_KP, PID_STRAIGHT_KI, PID_STRAIGHT_KD);
    setMotorLeft(-(currentSpeed + (int)correction));
    setMotorRight(-(currentSpeed - (int)correction));
  } 
  else if (currentCommand == "leftIntersection" || currentCommand == "rightIntersection" || currentCommand == "turn180") {

    float startHeading = robotHeading;

    float targetHeading = (currentCommand == "leftIntersection") ? startHeading - 90 : 
                          (currentCommand == "rightIntersection") ? startHeading + 90 : startHeading + 180;

    if (targetHeading > 180) targetHeading -= 360;
    if (targetHeading < -180) targetHeading += 360;
    
    stopMotors();
    if (currentCommand != "turn180") delay(150); 

    resetPid(targetHeading); 
    unsigned long startTime = millis();
    
    while (true) {
      if (millis() - startTime > 3000) break;
      updateMpu();
      
      float angleError = targetHeading - robotHeading;
      if (angleError > 180) angleError -= 360;
      if (angleError < -180) angleError += 360;

      // Usiamo angleError direttamente nel PID invece di target e current separati
      int turnSpeed = (int)constrain(
        computePid(angleError, 0, PID_TURN_KP, PID_TURN_KI, PID_TURN_KD), // Passiamo l'errore già calcolato
        -PID_TURN_MAX_SPEED, PID_TURN_MAX_SPEED
      );

      float factor = constrain(abs(angleError) / 90.0, 0.3, 1.0);
      turnSpeed *= factor;

      // Applica zone morte motori
      if (turnSpeed > 0 && turnSpeed < PID_TURN_MIN_SPEED) turnSpeed = PID_TURN_MIN_SPEED;
      if (turnSpeed < 0 && turnSpeed > -PID_TURN_MIN_SPEED) turnSpeed = -PID_TURN_MIN_SPEED;

      setMotorLeft(turnSpeed);
      setMotorRight(-turnSpeed);
      
      readSerial();
      if (currentCommand == "stop") break;
    }
    stopMotors();
    currentCommand = "";
  } 
  else {
    stopMotors();
  }
}

float updateMpu() {
  i2cMux.selectChannel(3);
  if (!imuReady) return robotHeading;
  
  imu::Vector<3> euler = mpuSensor.getVector(Adafruit_BNO055::VECTOR_EULER);
  float currentRawHeading = euler.x();
  float relativeHeading = currentRawHeading - headingOffset;
  if (relativeHeading > 180) relativeHeading -= 360;
  if (relativeHeading < -180) relativeHeading += 360;
  robotHeading = relativeHeading;
  return robotHeading;
}

void resetHeading() {
  i2cMux.selectChannel(3);
  if (!imuReady) return;
  
  imu::Vector<3> euler = mpuSensor.getVector(Adafruit_BNO055::VECTOR_EULER);
  headingOffset = euler.x();
  robotHeading = 0;
}

void initTofSensors() {
  i2cMux.selectChannel(5); tofFront.begin();
  i2cMux.selectChannel(7); tofLeft.begin();
  i2cMux.selectChannel(6); tofRight.begin();
  i2cMux.selectChannel(4); tofBack.begin();
}

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

void readSerial() {
  while (Serial.available() >= 2) {
    if (Serial.read() != 0xFF) continue;
    uint8_t cmd = Serial.read();
    switch (cmd) {
      case 2: currentCommand = "stop"; break;
      case 3: 
        while (Serial.available() < 2);
        currentOffset = (float)(int16_t)((Serial.read() << 8) | Serial.read());
        currentCommand = "drive";
        break;
      case 4: currentCommand = "backward"; break;
      case 7: currentCommand = "leftIntersection"; break;
      case 8: currentCommand = "rightIntersection"; break;
      case 9: currentCommand = "turn180"; break;
    }
  }
}

void sendSerial() {
  uint8_t payload[13];
  payload[0] = 0xAA;
  uint16_t front = (uint16_t)constrain(valTFront, 0, 65535);
  uint16_t left  = (uint16_t)constrain(valTLeft,  0, 65535);
  uint16_t right = (uint16_t)constrain(valTRight, 0, 65535);
  uint16_t back  = (uint16_t)constrain(valTBack,  0, 65535);
  memcpy(&payload[1], &front, 2); memcpy(&payload[3], &left, 2);
  memcpy(&payload[5], &right, 2); memcpy(&payload[7], &back, 2);
  memcpy(&payload[9], &robotHeading, 4);
  Serial.write(payload, 13);
}