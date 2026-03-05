#pragma once

#include <Arduino.h>

// ##########################################################################
// VERSIONE FIRMWARE                                                        #
// ##########################################################################

#define FIRMWARE_VERSION "1.1.1"

// ##########################################################################
// PIN MOTORI - 4 MOTORI DC (L298N)                                         #
// ##########################################################################

// MOTORE DAVANTI DESTRO
#define PIN_MOTOR_FR_IN1     14
#define PIN_MOTOR_FR_IN2     27
#define PIN_MOTOR_FR_PWM     12

// MOTORE DIETRO DESTRO
#define PIN_MOTOR_BR_IN1     26
#define PIN_MOTOR_BR_IN2     25
#define PIN_MOTOR_BR_PWM     33

// MOTORE DAVANTI SINISTRO
#define PIN_MOTOR_FL_IN1     18
#define PIN_MOTOR_FL_IN2     5
#define PIN_MOTOR_FL_PWM     19

// MOTORE DIETRO SINISTRO
#define PIN_MOTOR_BL_IN1     17
#define PIN_MOTOR_BL_IN2     16
#define PIN_MOTOR_BL_PWM     4

// ##########################################################################
// PIN ENCODER                                                              #
// ##########################################################################

#define PIN_ENCODER_L_A     34
#define PIN_ENCODER_L_B     35
#define PIN_ENCODER_R_A     36
#define PIN_ENCODER_R_B     39

// ##########################################################################
// PIN SENSORI I2C                                                          #
// ##########################################################################

#define PIN_I2C_SDA         21
#define PIN_I2C_SCL         22

#define ADDR_IMU            0x68
#define ADDR_COLOR          0x29
#define ADDR_TOF_DEFAULT    0x29
#define ADDR_TOF_NEW        0x30

#define PIN_TOF_XSHUT       4

// ##########################################################################
// PARAMETRI PWM (LEDC)                                                     #
// ##########################################################################

#define PWM_FREQ            5000
#define PWM_RESOLUTION      8

#define PWM_CHANNEL_MOTOR_FL 0
#define PWM_CHANNEL_MOTOR_FR 1
#define PWM_CHANNEL_MOTOR_BL 2
#define PWM_CHANNEL_MOTOR_BR 3

// ##########################################################################
// PARAMETRI MOTORI                                                         #
// ##########################################################################

#define MOTOR_MAX_PWM       255
#define MOTOR_MIN_PWM       0
#define MOTOR_DEADBAND      35
#define MOTOR_SAFE_START    45

// ##########################################################################
// PARAMETRI PID                                                            #
// ##########################################################################

#define PID_LINE_KP         1.8f
#define PID_LINE_KI         0.01f
#define PID_LINE_KD         0.15f

#define PID_OUTPUT_MAX      150
#define PID_OUTPUT_MIN      -150

// ##########################################################################
// SOGLIE SENSORI                                                           #
// ##########################################################################

#define PITCH_RAMP_THRESHOLD    12.0f
#define PITCH_SEESAW_THRESHOLD  18.0f

#define DISTANCE_OBSTACLE_MM    150
#define DISTANCE_VICTIM_MM      80

// ##########################################################################
// SERIAL COMMUNICATION                                                     #
// ##########################################################################

#define SERIAL_BAUD         115200
#define SERIAL_WATCHDOG_MS  500

// ##########################################################################
// TIMING LOOP                                                              #
// ##########################################################################

#define LOOP_PERIOD_MS      10
#define TELEMETRY_PERIOD_MS 50

// ##########################################################################
// DEBUG                                                                    #
// ##########################################################################

#ifdef DEBUG_MODE
  #define DEBUG_PRINT(x)   Serial.print(x)
  #define DEBUG_PRINTLN(x) Serial.println(x)
#else
  #define DEBUG_PRINT(x)
  #define DEBUG_PRINTLN(x)
#endif