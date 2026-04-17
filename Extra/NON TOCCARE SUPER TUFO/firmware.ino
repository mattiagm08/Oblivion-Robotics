
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

//OSTACOLO
int soglia_ostacolo = 250;

// CONFIGURAZIONE LED ILLUMINAZIONE

#define LED_PIN 32
int ledBrightness = 10;

// CONFIGURAZIONE PIN RESCUE ZONE

#define SILVER_LEFT 34
#define SILVER_RIGHT 13
#define PIN_BALL 35

#define PID_STRAIGHT_KP  1.5 //2.5 
#define PID_STRAIGHT_KI  0.0
#define PID_STRAIGHT_KD  0.45 

#define PID_TURN_KP       4.0 //4.0
#define PID_TURN_KI       0.0
#define PID_TURN_KD       1.0

#define PID_TURN_THRESHOLD   3.0
#define PID_TURN_MIN_SPEED   80
#define PID_TURN_MAX_SPEED   125 

#define TURN_SPEED 180
#define TURN_KP_TEST 4.5

TCA9548 i2cMux(0x70);
Adafruit_VL53L0X tofFront = Adafruit_VL53L0X();
Adafruit_VL53L0X tofLeft  = Adafruit_VL53L0X();
Adafruit_VL53L0X tofRight = Adafruit_VL53L0X();
Adafruit_VL53L0X tofBack  = Adafruit_VL53L0X();
Adafruit_BNO055 mpuSensor = Adafruit_BNO055(55, 0x29);

float valTFront = 0, valTLeft = 0, valTRight = 0, valTBack = 0;
float headingOffset = 0;
float robotHeading = 0;
unsigned long lastMPUTime = 0;
unsigned long lastSensorMillis = 0;
const int sensorInterval = 50;

bool imuReady = false;
bool imuStable = false;

float pidIntegral  = 0;
float pidPrevError = 0;
float pidSetpoint  = 0;
unsigned long pidLastTime = 0;

String currentCommand = "";
int    currentSpeed   = 0;
float  currentOffset  = 0;
float  pendingOffset  = 0;
bool   waitForOffset  = false;

enum TurnState {
  TURN_NONE,
  TURN_LEFT_90,
  TURN_RIGHT_90,
  TURN_180
};

TurnState turnState = TURN_NONE;
float turnStartHeading = 0;
float turnTargetHeading = 0;
bool turnInitialized = false;

unsigned long noIntersectionUntil = 0;

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);
  Wire.setClock(100000);
  pinMode(PIN_BALL, INPUT);

  initializeMotors();
  stopMotors();
  analogWrite(LED_PIN, ledBrightness);

  pinMode(SILVER_LEFT, INPUT);
  pinMode(SILVER_RIGHT, INPUT);
  pinMode(23, OUTPUT);
  digitalWrite(23, LOW);

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
  if(valTFront <= 50) Obstacle();
  if(!digitalRead(SILVER_LEFT) || !digitalRead(SILVER_RIGHT)) isArgento();
  if((digitalRead(SILVER_LEFT)) && digitalRead(SILVER_RIGHT)) digitalWrite(23, LOW);
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

int lastTurnDirection = 0; 
bool maneuverLock = false;

void moveRobot() {
  static String prevCommand = "";

  if (currentCommand != prevCommand) {
    resetPid(robotHeading);
    prevCommand = currentCommand;
  }

  if (turnState != TURN_NONE) return;
  if (maneuverLock) return;

  if (currentCommand == "drive") {
    currentSpeed = 125;
    float correction = computePid(0, currentOffset, PID_STRAIGHT_KP, PID_STRAIGHT_KI, PID_STRAIGHT_KD);
    
    int adaptiveSpeed = currentSpeed;
    if (abs(currentOffset) > 150) adaptiveSpeed = 120; 

    setMotorLeft(adaptiveSpeed - (int)correction);
    setMotorRight(adaptiveSpeed + (int)correction);
  } 
  else if (currentCommand == "forward") {
    currentSpeed = 150; 
    float correction = computePid(pidSetpoint, robotHeading, PID_STRAIGHT_KP, PID_STRAIGHT_KI, PID_STRAIGHT_KD);
    setMotorLeft(currentSpeed - (int)correction);
    setMotorRight(currentSpeed + (int)correction);
  }
  else if (currentCommand == "backward") {
    currentSpeed = 125;
    float correction = computePid(pidSetpoint, robotHeading, PID_STRAIGHT_KP, PID_STRAIGHT_KI, PID_STRAIGHT_KD);
    setMotorLeft(-(currentSpeed + (int)correction));
    setMotorRight(-(currentSpeed - (int)correction));
  } 
  else if (currentCommand == "left") {
    currentSpeed = 180;
    setMotorLeft(-currentSpeed);
    setMotorRight(currentSpeed);
  } 
  else if (currentCommand == "right") {
    currentSpeed = 180;
    setMotorLeft(currentSpeed);
    setMotorRight(-currentSpeed);
  } 
  else if (currentCommand == "leftIntersection") {
    currentSpeed = 200;
    maneuverLock = true;
    stopMotors();
    delay(100);

    setMotorLeft(-30);
    setMotorRight(-30);
    delay(50);

    setMotorLeft(150); 
    setMotorRight(150);
    delay(370);

    float targetHeading = robotHeading - 65.0;
    if (targetHeading < -180) targetHeading += 360;

    float error = 100;

    while (abs(error) > 2.0) {
        updateMpu();
        Serial.println(float(updateMpu()));
        error = targetHeading - robotHeading;
        if (error > 180) error -= 360;
        if (error < -180) error += 360;

        setMotorLeft(-currentSpeed);
        setMotorRight(currentSpeed);
    }

    stopMotors();

    setMotorLeft(150);
    setMotorRight(150);
    delay(150);
    
    pidSetpoint = robotHeading;
    currentCommand = "drive";
    maneuverLock = false;
    noIntersectionUntil = millis() + 2000;
    waitForOffset = true;
  }

  else if (currentCommand == "rightIntersection") {
    currentSpeed = 200;
    maneuverLock = true;
    stopMotors();
    delay(100);

    setMotorLeft(-30);
    setMotorRight(-30);
    delay(50);

    setMotorLeft(150);
    setMotorRight(150);
    delay(370);

    float targetHeading = robotHeading + 65.0;
    if (targetHeading > 180) targetHeading -= 360;

    float error = 100;

    while (abs(error) > 2.0) {
        updateMpu();
        error = targetHeading - robotHeading;
        if (error > 180) error -= 360;
        if (error < -180) error += 360;

        setMotorLeft(currentSpeed);
        setMotorRight(-currentSpeed);
    }

    stopMotors();

    setMotorLeft(150);
    setMotorRight(150);
    delay(150);

    pidSetpoint = robotHeading;
    currentCommand = "drive";
    maneuverLock = false;
    noIntersectionUntil = millis() + 2000;
    waitForOffset = true;
  }

  else if (currentCommand == "turn180") {
    maneuverLock = true;
    stopMotors();
    delay(100);

    setMotorLeft(-30);
    setMotorRight(-30);
    delay(50);

    setMotorLeft(150);
    setMotorRight(150);
    delay(150);

    float targetHeading = robotHeading + 180.0;
    if (targetHeading > 180) targetHeading -= 360;

    currentSpeed = 200;
    float error = 100;

    while (abs(error) > 3.0) {
        updateMpu();
        error = targetHeading - robotHeading;
        if (error > 180) error -= 360;
        if (error < -180) error += 360;

        setMotorLeft(-currentSpeed);
        setMotorRight(currentSpeed);
    }

    stopMotors();

    setMotorLeft(150);
    setMotorRight(150);
    delay(150);

    pidSetpoint = robotHeading;
    currentCommand = "drive";
    maneuverLock = false;
    noIntersectionUntil = millis() + 2000;
    waitForOffset = true;
  } else {
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

    if ((cmd == 7 || cmd == 8 || cmd == 9) && millis() < noIntersectionUntil) continue;

    switch (cmd) {
      case 2: currentCommand = "stop"; break;
      case 3: 
        while (Serial.available() < 2);
        pendingOffset = (float)(int16_t)((Serial.read() << 8) | Serial.read());
        if (waitForOffset) {
          currentOffset = pendingOffset;
          currentCommand = "drive";
        } else {
          currentOffset = pendingOffset;
          currentCommand = "drive";
        }
        break;
      case 4: currentCommand = "backward"; break;
      case 7: currentCommand = "leftIntersection"; break;
      case 8: currentCommand = "rightIntersection"; break;
      case 9: currentCommand = "turn180"; break;
      case 12: {
        int val = digitalRead(PIN_BALL);
        Serial.write(0xBB);
        Serial.write(val ? 1 : 0);
        break;
      }
      case 13: currentCommand = "forward"; break; 
      case 14: currentCommand = "left"; break;
      case 15: currentCommand = "right"; break;
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

void Obstacle(){
  
  bool isEnded = false;
  bool Gulp = false;

      stopMotors();
      delay(100);

      setMotorLeft(-30);
      setMotorRight(-30);
      delay(50);

      setMotorLeft(-150); 
      setMotorRight(-150); 
      delay(185);

      stopMotors();
      delay(100);

      setMotorLeft(30);
      setMotorRight(30);
      delay(50);

      float targetHeading = robotHeading + 90.0;
      if (targetHeading > 180) targetHeading -= 360;

      currentSpeed = 200;
      float error = 100;

      while (abs(error) > 3.0) {
          updateMpu();
          error = targetHeading - robotHeading;
          if (error > 180) error -= 360;
          if (error < -180) error += 360;

          setMotorLeft(currentSpeed);
          setMotorRight(-currentSpeed);
      }

      stopMotors();
      pidSetpoint = robotHeading;
      currentCommand = "";

      currentSpeed = 200;
      stopMotors();
      delay(100);

      setMotorLeft(-30);
      setMotorRight(-30);
      delay(50);

      while (valTLeft < soglia_ostacolo) {
        updateTof();
        setMotorLeft(200); 
        setMotorRight(200); 
      }

      setMotorLeft(150); 
      setMotorRight(150);
      delay(700);

      targetHeading = robotHeading - 90.0;
      if (targetHeading < -180) targetHeading += 360;

      error = 100;

      while (abs(error) > 2.0) {
          updateMpu();
          Serial.println(float(updateMpu()));
          error = targetHeading - robotHeading;
          if (error > 180) error -= 360;
          if (error < -180) error += 360;

          setMotorLeft(-currentSpeed);
          setMotorRight(currentSpeed);
      }

      stopMotors();

      pidSetpoint = robotHeading;
      currentCommand = "";

    Gulp = false;

  while(!isEnded){
    updateTof();
    currentSpeed = 150;

    setMotorLeft(currentSpeed);
    setMotorRight(currentSpeed);

    if(valTLeft < soglia_ostacolo ) Gulp = true;
    

    else if(valTLeft > soglia_ostacolo && Gulp){
      isEnded = true;
  
    }

  }

      setMotorLeft(150);
      setMotorRight(150);
      delay(400);

      stopMotors();
      delay(100);

      

      setMotorLeft(-30);
      setMotorRight(-30);
      delay(50);

      targetHeading = robotHeading - 90.0;
      if (targetHeading > 180) targetHeading -= 360;

      currentSpeed = 200;
      error = 100;

      while (abs(error) > 3.0) {
          updateMpu();
          error = targetHeading - robotHeading;
          if (error > 180) error -= 360;
          if (error < -180) error += 360;

          setMotorLeft(-currentSpeed);
          setMotorRight(currentSpeed);
      }

      stopMotors();
      pidSetpoint = robotHeading;
      currentCommand = "";

      currentSpeed = 200;
      stopMotors();
      delay(100);

      setMotorLeft(-30);
      setMotorRight(-30);
      delay(50);

      while (valTLeft > soglia_ostacolo) {
        updateTof();
        setMotorLeft(150);
        setMotorRight(150);
      }

      setMotorLeft(150);
      setMotorRight(150);
      delay(400);

      targetHeading = robotHeading + 90.0;
      if (targetHeading < -180) targetHeading += 360;

      error = 100;

      while (abs(error) > 3.0) {
          updateMpu();
          error = targetHeading - robotHeading;
          if (error > 180) error -= 360;
          if (error < -180) error += 360;

          setMotorLeft(currentSpeed);
          setMotorRight(-currentSpeed);
      }

      stopMotors();

      setMotorLeft(-150);
      setMotorRight(-150);
      delay(500);
      
      pidSetpoint = robotHeading;
      currentCommand = "drive";
}

void isArgento(){
  digitalWrite(23, HIGH);
  setMotorLeft(-30);
  setMotorRight(-30);
  delay(120);
  stopMotors();
  delay(1000);  //1 sec di delay

  if(!digitalRead(SILVER_LEFT) && !digitalRead(SILVER_RIGHT)){
    setMotorLeft(150);
    setMotorRight(150);
    delay(500);
    digitalWrite(23, HIGH);
    
  }else{
    if(!digitalRead(SILVER_LEFT)){
      setMotorLeft(0);
      setMotorRight(150);

      digitalWrite(23, HIGH);
    }
    else if(!digitalRead(SILVER_RIGHT)){
      setMotorLeft(150);
      setMotorRight(0);

      digitalWrite(23, HIGH);
    }
  }
}