
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
#define ENA_L 19  
#define IN1_L 18
#define IN2_L 5
#define ENB_L 4   
#define IN3_L 17
#define IN4_L 16

// STRUTTURA PID

struct PID {
  float kp;
  float ki;
  float kd;
  float integral;
  float prevError;
  float prevDerivative;
  float integralLimit;
  float alpha;
  unsigned long lastTime;
};

// ISTANZE PID: MANTENIMENTO RETTILINEO E CONTROLLO ROTAZIONE

PID pidDrive = { 2.2f, 0.09f, 0.45f, 0.0f, 0.0f, 0.0f, 40.0f, 0.30f, 0 };
PID pidTurn = { 3.5f, 0.06f, 0.70f, 0.0f, 0.0f, 0.0f, 30.0f, 0.20f, 0 };

// ISTANZE DEI SENSORI E DEL MULTIPLEXER I2C

TCA9548 i2cMux(0x70);
Adafruit_VL53L0X tofFront = Adafruit_VL53L0X();
Adafruit_VL53L0X tofLeft = Adafruit_VL53L0X();
Adafruit_VL53L0X tofRight = Adafruit_VL53L0X();
Adafruit_MPU6050 mpuSensor;

// VARIABILI GLOBALI PER SENSORI, ORIENTAMENTO E TIMING

float valTFront = 0, valTLeft = 0, valTRight = 0;
float gyroZOffset = 0;
float robotHeading = 0;
unsigned long lastMPUMicros = 0;
unsigned long lastSensorMillis = 0;
int sensorInterval = 50;

// STRUTTURA E CODA PER COMUNICAZIONE TRA I DUE CORE

struct Command {
  char cmd[32];
  int speed;
};
QueueHandle_t commandQueue;

// VARIABILI GLOBALI PER LA LOGICA MOTORE

String currentCommand = "";
String prevCommand = "";
int currentSpeed = 0;

// HEADING TARGET PER MANOVRE CONTROLLATE DAL PID

float targetDriveHeading = 0;
float targetTurnHeading = 0;

// NORMALIZZAZIONE ANGOLO TRA -180 E 180

float normalizeAngle(float angle) {
  while (angle > 180.0f) angle -= 360.0f;
  while (angle < -180.0f) angle += 360.0f;
  return angle;
}

// INIZIALIZZAZIONE PIN DEI MOTORI COME OUTPUT

void initializeMotors() {
  pinMode(ENA_R, OUTPUT); pinMode(IN1_R, OUTPUT); pinMode(IN2_R, OUTPUT);
  pinMode(IN3_R, OUTPUT); pinMode(IN4_R, OUTPUT); pinMode(ENB_R, OUTPUT);
  pinMode(ENA_L, OUTPUT); pinMode(IN1_L, OUTPUT); pinMode(IN2_L, OUTPUT);
  pinMode(IN3_L, OUTPUT); pinMode(IN4_L, OUTPUT); pinMode(ENB_L, OUTPUT);
}

// FUNZIONE PER ARRESTARE IMMEDIATAMENTE TUTTI I MOTORI

void stopMotors() {
  digitalWrite(IN1_R, LOW); digitalWrite(IN2_R, LOW);
  digitalWrite(IN3_R, LOW); digitalWrite(IN4_R, LOW);
  digitalWrite(IN1_L, LOW); digitalWrite(IN2_L, LOW);
  digitalWrite(IN3_L, LOW); digitalWrite(IN4_L, LOW);
  analogWrite(ENA_R, 0); analogWrite(ENB_R, 0);
  analogWrite(ENA_L, 0); analogWrite(ENB_L, 0);
}

// CONTROLLO PWM E DIREZIONE MOTORI DESTRI

void setMotorRight(int pwm) {
  if (pwm >= 0) {
    digitalWrite(IN1_R, LOW);  digitalWrite(IN2_R, HIGH);
    digitalWrite(IN3_R, HIGH); digitalWrite(IN4_R, LOW);
  } else {
    digitalWrite(IN1_R, HIGH); digitalWrite(IN2_R, LOW);
    digitalWrite(IN3_R, LOW);  digitalWrite(IN4_R, HIGH);
    pwm = -pwm;
  }
  analogWrite(ENA_R, constrain(pwm, 0, 255));
  analogWrite(ENB_R, constrain(pwm, 0, 255));
}

// CONTROLLO PWM E DIREZIONE MOTORI SINISTRI

void setMotorLeft(int pwm) {
  if (pwm >= 0) {
    digitalWrite(IN1_L, HIGH); digitalWrite(IN2_L, LOW);
    digitalWrite(IN3_L, LOW);  digitalWrite(IN4_L, HIGH);
  } else {
    digitalWrite(IN1_L, LOW);  digitalWrite(IN2_L, HIGH);
    digitalWrite(IN3_L, HIGH); digitalWrite(IN4_L, LOW);
    pwm = -pwm;
  }
  analogWrite(ENA_L, constrain(pwm, 0, 255));
  analogWrite(ENB_L, constrain(pwm, 0, 255));
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
  i2cMux.selectChannel(1);
  sensors_event_t accel, gyro, temp;
  mpuSensor.getEvent(&accel, &gyro, &temp);
  
  unsigned long currentTime = micros();
  if (lastMPUMicros == 0) lastMPUMicros = currentTime;
  float dt = (currentTime - lastMPUMicros) / 1000000.0f;
  lastMPUMicros = currentTime;
  
  float gyroZ = gyro.gyro.z - gyroZOffset;
  if (abs(gyroZ) < 0.03) gyroZ = 0;
  
  robotHeading += (gyroZ * 180.0f / PI) * dt;
  robotHeading = normalizeAngle(robotHeading);
  return robotHeading;
}

// ATTIVAZIONE DEI SENSORI ToF TRAMITE I CANALI DEL MULTIPLEXER

void initTofSensors() {
  i2cMux.selectChannel(7); tofFront.begin();
  i2cMux.selectChannel(6); tofLeft.begin();
  i2cMux.selectChannel(5); tofRight.begin();
}

// LETTURA SEQUENZIALE DEI SENSORI DI DISTANZA ToF

void updateTof() {
  if (millis() - lastSensorMillis < sensorInterval) return;
  lastSensorMillis = millis();
  VL53L0X_RangingMeasurementData_t measure;
  i2cMux.selectChannel(7); tofFront.rangingTest(&measure, false);
  valTFront = (measure.RangeStatus != 4) ? measure.RangeMilliMeter : 999;
  i2cMux.selectChannel(6); tofLeft.rangingTest(&measure, false);
  valTLeft = (measure.RangeStatus != 4) ? measure.RangeMilliMeter : 999;
  i2cMux.selectChannel(5); tofRight.rangingTest(&measure, false);
  valTRight = (measure.RangeStatus != 4) ? measure.RangeMilliMeter : 999;
}

// FUNZIONE PER PULIZIA CODA E ASSESTAMENTO DOPO MANOVRA

void finalizeManeuver() {
  stopMotors();
  delay(150);
  Command dummyCmd;
  while (xQueueReceive(commandQueue, &dummyCmd, 0));
  currentCommand = "";
  prevCommand = "";
  currentSpeed = 0;
}

// RESET STATO INTERNO PID

void resetPID(PID &pid) {
  pid.integral = 0.0f;
  pid.prevError = 0.0f;
  pid.prevDerivative = 0.0f;
  pid.lastTime = millis();
}

// CALCOLO OUTPUT PID CON ANTI-WINDUP E FILTRO DERIVATIVO

float computePID(PID &pid, float error) {
  unsigned long now = millis();
  float dt = (now - pid.lastTime) / 1000.0f;
  if (dt <= 0.0f || dt > 0.5f) dt = 0.01f;
  pid.lastTime = now;

  pid.integral += error * dt;
  pid.integral = constrain(pid.integral, -pid.integralLimit, pid.integralLimit);

  float rawDerivative = (error - pid.prevError) / dt;
  float filtDerivative = pid.alpha * rawDerivative + (1.0f - pid.alpha) * pid.prevDerivative;
  pid.prevDerivative = filtDerivative;
  pid.prevError = error;

  return (pid.kp * error) + (pid.ki * pid.integral) + (pid.kd * filtDerivative);
}

// LOGICA DI MOVIMENTO

void moveRobot() {

  if (currentCommand != prevCommand) {

    if (currentCommand == "avanti" || currentCommand == "indietro") {
      targetDriveHeading = robotHeading;
      resetPID(pidDrive);
    }

    else if (currentCommand == "destra") {
      targetTurnHeading = normalizeAngle(robotHeading + 90.0f);
      resetPID(pidTurn);
    }

    else if (currentCommand == "sinistra") {
      targetTurnHeading = normalizeAngle(robotHeading - 90.0f);
      resetPID(pidTurn);
    }

    prevCommand = currentCommand;
  }

  if (currentCommand == "avanti") {

    float error = normalizeAngle(targetDriveHeading - robotHeading);
    float correction = computePID(pidDrive, error);
    correction = constrain(correction, -60.0f, 60.0f);
    setMotorLeft (constrain((int)(210 + correction), 0, 255));
    setMotorRight(constrain((int)(210 - correction), 0, 255));

  }

  else if (currentCommand == "indietro") {

    float error = normalizeAngle(targetDriveHeading - robotHeading);
    float correction = computePID(pidDrive, error);
    correction = constrain(correction, -60.0f, 60.0f);
    setMotorLeft(-constrain((int)(150 + correction), 0, 255));
    setMotorRight(-constrain((int)(150 - correction), 0, 255));

  }

  else if (currentCommand == "destra") {

    float error = normalizeAngle(targetTurnHeading - robotHeading);
    float output = computePID(pidTurn, error);
    output = constrain(output, -220.0f, 220.0f);

    if (abs(output) < 30) output = 0;

    if (abs(error) > 2.5f) {
      int pwm = abs((int)output);
      if (error > 0) {
        setMotorLeft(pwm);
        setMotorRight(-pwm);
      } else {
        setMotorLeft(-pwm);
        setMotorRight(pwm);
      }
    } else {
      finalizeManeuver();
    }

  }

  else if (currentCommand == "sinistra") {

    float error = normalizeAngle(targetTurnHeading - robotHeading);
    float output = computePID(pidTurn, error);
    output = constrain(output, -220.0f, 220.0f);

    if (abs(output) < 30) output = 0;

    if (abs(error) > 2.5f) {
      int pwm = abs((int)output);
      if (error > 0) {
        setMotorLeft(pwm);
        setMotorRight(-pwm);
      } else {
        setMotorLeft(-pwm);
        setMotorRight(pwm);
      }
    } else {
      finalizeManeuver();
    }

  }

  else if (currentCommand == "incrociodx") {

    stopMotors();
    delay(1500);
    setMotorLeft(210);
    setMotorRight(210);
    delay(350);

    float turnTarget = normalizeAngle(robotHeading + 90.0f);
    resetPID(pidTurn);
    unsigned long startTime = millis();

    while (millis() - startTime < 3000) {
      updateMpu();
      float error = normalizeAngle(turnTarget - robotHeading);
      float output = computePID(pidTurn, error);
      output = constrain(output, -220.0f, 220.0f);

      if (abs(output) < 30) output = 0;

      if (abs(error) <= 2.5f) break;

      int pwm = abs((int)output);
      if (error > 0) {
        setMotorLeft(pwm);
        setMotorRight(-pwm);
      } else {
        setMotorLeft(-pwm);
        setMotorRight(pwm);
      }

      delay(1);
    }

    finalizeManeuver();

  }

  else if (currentCommand == "incrociosx") {

    stopMotors();
    delay(1500);
    setMotorLeft(210);
    setMotorRight(210);
    delay(350);

    float turnTarget = normalizeAngle(robotHeading - 90.0f);
    resetPID(pidTurn);
    unsigned long startTime = millis();

    while (millis() - startTime < 3000) {
      updateMpu();
      float error = normalizeAngle(turnTarget - robotHeading);
      float output = computePID(pidTurn, error);
      output = constrain(output, -220.0f, 220.0f);

      if (abs(output) < 30) output = 0;

      if (abs(error) <= 2.5f) break;

      int pwm = abs((int)output);
      if (error > 0) {
        setMotorLeft(pwm);
        setMotorRight(-pwm);
      } else {
        setMotorLeft(-pwm);
        setMotorRight(pwm);
      }

      delay(1);
    }

    finalizeManeuver();

  }

  else if (currentCommand == "inversione") {

    float turnTarget = normalizeAngle(robotHeading + 180.0f);
    resetPID(pidTurn);
    unsigned long startTime = millis();

    while (millis() - startTime < 4000) {
      updateMpu();
      float error = normalizeAngle(turnTarget - robotHeading);
      float output = computePID(pidTurn, error);
      output = constrain(output, -220.0f, 220.0f);

      if (abs(output) < 30) output = 0;

      if (abs(error) <= 2.5f) break;

      int pwm = abs((int)output);
      if (error > 0) {
        setMotorLeft(pwm);
        setMotorRight(-pwm);
      } else {
        setMotorLeft(-pwm);
        setMotorRight(pwm);
      }

      delay(1);
    }

    finalizeManeuver();

  }

  else {
    stopMotors();
  }
}

// SERIAL TASK: GESTIONE SERIALE E COMUNICAZIONE (CORE 0)

void serialTaskFunc(void *pvParameters) {
  String serialBuffer = "";
  for (;;) {
    while (Serial.available()) {
      char c = Serial.read();
      if (c == '\n') {
        serialBuffer.trim();
        if (serialBuffer.length() > 0) {
          Command newCmd;
          int sepIndex = serialBuffer.indexOf(':');
          if (sepIndex != -1) {
            String tempCmd = serialBuffer.substring(0, sepIndex);
            tempCmd.toCharArray(newCmd.cmd, sizeof(newCmd.cmd));
            newCmd.speed = serialBuffer.substring(sepIndex + 1).toInt();
          }

          else if (serialBuffer == "START") {
            strcpy(newCmd.cmd, "avanti");
            newCmd.speed = 0;
          }

          else if (serialBuffer == "stop") {
            strcpy(newCmd.cmd, "stop");
            newCmd.speed = 0;
          } else {
            serialBuffer.toCharArray(newCmd.cmd, sizeof(newCmd.cmd));
            newCmd.speed = 0;
          }

          xQueueSend(commandQueue, &newCmd, portMAX_DELAY);
        }
        serialBuffer = "";
      } else {
        serialBuffer += c;
      }
    }

    static unsigned long lastSendTime = 0;
    if (millis() - lastSendTime > 100) {
      Serial.print("H:");  Serial.print(robotHeading);
      Serial.print("|TF:"); Serial.print(valTFront);
      Serial.print("|TS:"); Serial.print(valTLeft);
      Serial.print("|TD:"); Serial.println(valTRight);
      lastSendTime = millis();
    }

    vTaskDelay(10 / portTICK_PERIOD_MS);
  }
}

// MOTOR TASK: CICLO CONTINUO SENSORI E MOTORI (CORE 1)

void motorTaskFunc(void *pvParameters) {
  Command receivedCmd;
  for (;;) {
    if (xQueueReceive(commandQueue, &receivedCmd, 0)) {
      currentCommand = String(receivedCmd.cmd);
    }

    updateMpu();
    moveRobot();
    updateTof();

    vTaskDelay(1 / portTICK_PERIOD_MS);
  }
}

// SETUP: CONFIGURAZIONE ED AVVIO TASK CORE

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);
  Wire.setClock(100000);

  initializeMotors();
  stopMotors();

  if (!i2cMux.begin()) Serial.println("ERRORE MULTIPLEXER");

  i2cMux.selectChannel(1);
  if (mpuSensor.begin()) {
    mpuSensor.setGyroRange(MPU6050_RANGE_250_DEG);
    mpuSensor.setFilterBandwidth(MPU6050_BAND_21_HZ);
    calibrateMpu();
  }

  initTofSensors();
  lastMPUMicros = micros();

  commandQueue = xQueueCreate(10, sizeof(Command));

  xTaskCreatePinnedToCore(serialTaskFunc, "SerialTask", 8192, NULL, 1, NULL, 0);
  xTaskCreatePinnedToCore(motorTaskFunc, "MotorTask",  8192, NULL, 2, NULL, 1);
}

void loop() {
}