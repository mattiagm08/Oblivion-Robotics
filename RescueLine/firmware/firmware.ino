
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
unsigned long lastMPUTime = 0;
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
int currentSpeed = 0;

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
  currentSpeed = 0;
}

// LOGICA DI MOVIMENTO 

void moveRobot() {
  
  // [AVANTI]

  if (currentCommand == "avanti") {

    currentSpeed = 210; 
    setMotorLeft(currentSpeed);
    setMotorRight(currentSpeed);

  } 
  
  // [INDIETRO]

  else if (currentCommand == "indietro") {

    currentSpeed = 150;
    setMotorLeft(-currentSpeed);
    setMotorRight(-currentSpeed);

  } 
  
  // [DESTRA]
  
  else if (currentCommand == "destra") {

    currentSpeed = 200;
    setMotorLeft(currentSpeed);
    setMotorRight(-currentSpeed);

  } 
  
  // [SINISTRA]
  
  else if (currentCommand == "sinistra") {

    currentSpeed = 200; 
    setMotorLeft(-currentSpeed);
    setMotorRight(currentSpeed);

  }

  // [INCROCIO DESTRO]

  else if (currentCommand == "incrociodx") {

    stopMotors();
    delay(1500);
    currentSpeed = 210; 
    setMotorLeft(currentSpeed);
    setMotorRight(currentSpeed);
    delay(350); 
    currentSpeed = 200;
    float startHeading = robotHeading;
    while (robotHeading < startHeading + 45) {
      updateMpu();
      setMotorLeft(currentSpeed);
      setMotorRight(-currentSpeed);
      delay(1);
    }
    finalizeManeuver();

  }

  // [INCROCIO SINISTRO]

  else if (currentCommand == "incrociosx") {

    stopMotors();
    delay(1500);
    currentSpeed = 210;
    setMotorLeft(currentSpeed);
    setMotorRight(currentSpeed);
    delay(350); 
    currentSpeed = 200;
    float startHeading = robotHeading;
    while (robotHeading > startHeading - 45) {
      updateMpu();
      setMotorLeft(-currentSpeed);
      setMotorRight(currentSpeed);
      delay(1);
    }
    finalizeManeuver();

  }

  // [INVERSIONE]

  else if (currentCommand == "inversione") {

    currentSpeed = 200;
    float startHeading = robotHeading;
    while (robotHeading < startHeading + 180) {
      updateMpu();
      setMotorLeft(currentSpeed);
      setMotorRight(-currentSpeed);
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
    while(Serial.available()) {
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

          // [AVVIO]

          else if (serialBuffer == "START") {
            strcpy(newCmd.cmd, "avanti");
            newCmd.speed = 0;
          }
          
          // [STOP]

          else if (serialBuffer == "stop") {
            strcpy(newCmd.cmd, "stop");
            newCmd.speed = 0;
          } else {
            serialBuffer.toCharArray(newCmd.cmd, sizeof(newCmd.cmd));
            newCmd.speed = 0;
          }

          // INVIO COMANDO TASK MOTORI

          xQueueSend(commandQueue, &newCmd, portMAX_DELAY);
        }
        serialBuffer = "";
      } else {
        serialBuffer += c;
      }
    }

    // INVIO DATI COMUNICAZIONE SERIALE (100ms)

    static unsigned long lastSendTime = 0;
    if (millis() - lastSendTime > 100) {
      Serial.print("H:"); Serial.print(robotHeading);
      Serial.print("|TF:"); Serial.print(valTFront);
      Serial.print("|TS:"); Serial.print(valTLeft);
      Serial.print("|TD:");  Serial.println(valTRight);
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

      // VELOCITA' CMD.SPEED IGNORATA, GESTITA DALL'ESP
    }

    // FLUSSO: UPDATE MPU => MOVE => UPDATE ToF

    updateMpu();
    moveRobot();
    updateTof();

    // DELAY 1ms PER WATCHDOG RESET SENZA INTERFERENZA VELOCITA' REALE

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
  lastMPUTime = millis();

  // CODA PER SCAMBIARE I COMANDI TRA I CORE

  commandQueue = xQueueCreate(10, sizeof(Command));

  // ASSEGNAZIONE DEI TASK AI CORE SPECIFICI

  xTaskCreatePinnedToCore(serialTaskFunc, "SerialTask", 8192, NULL, 1, NULL, 0); // SerialTask ... 0 (CORE 0)
  xTaskCreatePinnedToCore(motorTaskFunc, "MotorTask", 8192, NULL, 2, NULL, 1);   // MotorTask ... 1 (CORE 1)
}

void loop() {
  // LAVORO GESTITO IN SERIAL TASK E MOTOR TASK
}