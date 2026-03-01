#pragma once

#include <Arduino.h>

/*
###########################################################################
# VERSIONE FIRMWARE                                                       #
###########################################################################
*/
#define FIRMWARE_VERSION "1.1.1"


/*
###########################################################################
# PIN MOTORI                                                              #
###########################################################################
# PONTE H DUAL (ES. L298N O DRV8833)                                      #
###########################################################################
*/

// MOTORE SINISTRO
#define PIN_MOTOR_L_IN1     25
#define PIN_MOTOR_L_IN2     26
#define PIN_MOTOR_L_PWM     27

// MOTORE DESTRO
#define PIN_MOTOR_R_IN1     32
#define PIN_MOTOR_R_IN2     33
#define PIN_MOTOR_R_PWM     14


/*
###########################################################################
# PIN ENCODER                                                             #
###########################################################################
# NOTA: PIN 34, 35, 36, 39 SONO SOLO INPUT (GPI) - PERFETTI PER ENCODER   #
###########################################################################
*/
#define PIN_ENCODER_L_A     34
#define PIN_ENCODER_L_B     35
#define PIN_ENCODER_R_A     36
#define PIN_ENCODER_R_B     39


/*
###########################################################################
# PIN SENSORI I2C                                                         #
###########################################################################
# SDA E SCL STANDARD ESP32                                                #
###########################################################################
*/
#define PIN_I2C_SDA         21
#define PIN_I2C_SCL         22

// INDIRIZZI I2C DISPOSITIVI
#define ADDR_IMU            0x68    // MPU6050
#define ADDR_COLOR          0x29    // TCS34725
#define ADDR_TOF_DEFAULT    0x29    // INDIRIZZO DI FABBRICA VL53L0X
#define ADDR_TOF_NEW        0x30    // NUOVO INDIRIZZO DOPO ASSEGNAZIONE XSHUT

// PIN DI CONTROLLO PER RISOLVERE CONFLITTO I2C (XSHUT)
#define PIN_TOF_XSHUT       4       // USATO PER CAMBIARE INDIRIZZO AL BOOT


/*
###########################################################################
# PIN ATTUATORI                                                           #
###########################################################################
*/
#define PIN_SERVO_ARM       13
#define PIN_SERVO_GRIP      12


/*
###########################################################################
# PARAMETRI PWM (LEDC)                                                    #
###########################################################################
*/
#define PWM_FREQ            5000    // 5KHZ PER I MOTORI
#define PWM_FREQ_SERVO      50      // 50HZ PER I SERVO
#define PWM_RESOLUTION      8       // 0-255

#define PWM_CHANNEL_MOTOR_L 0
#define PWM_CHANNEL_MOTOR_R 1
#define PWM_CHANNEL_SERVO_A 2
#define PWM_CHANNEL_SERVO_G 3


/*
###########################################################################
# PARAMETRI MOTORI                                                        #
###########################################################################
*/
#define MOTOR_MAX_PWM       255
#define MOTOR_MIN_PWM       0
#define MOTOR_DEADBAND      35      // PWM MINIMO PER VINCERE L'ATTRITO STATICO
#define MOTOR_SAFE_START    45      // SPINTA INIZIALE PER PARTENZE DOLCI


/*
###########################################################################
# PARAMETRI PID                                                           #
###########################################################################
# KP ALTA PER REATTIVITÀ SU LINEA, KD PER SMORZARE OSCILLAZIONI           #
###########################################################################
*/

// PID LINE FOLLOWING
#define PID_LINE_KP         1.8f    // VALORE NORMALIZZATO
#define PID_LINE_KI         0.01f
#define PID_LINE_KD         0.15f

// LIMITI OUTPUT PID (STERZATA MASSIMA)
#define PID_OUTPUT_MAX      150
#define PID_OUTPUT_MIN      -150


/*
###########################################################################
# SOGLIE SENSORI                                                          #
###########################################################################
*/
#define PITCH_RAMP_THRESHOLD    12.0f   // GRADI PER RILEVARE RAMPA
#define PITCH_SEESAW_THRESHOLD  18.0f   // GRADI PER RILEVARE ALTALENA

#define DISTANCE_OBSTACLE_MM    150
#define DISTANCE_VICTIM_MM      80


/*
###########################################################################
# SERIAL COMMUNICATION                                                    #
###########################################################################
*/
#define SERIAL_BAUD         115200
#define SERIAL_WATCHDOG_MS  500     // STOP MOTORI SE SERIALE PERSA


/*
###########################################################################
# TIMING LOOP                                                             #
###########################################################################
*/
#define LOOP_PERIOD_MS      10      // 100 HZ (LOOP PRINCIPALE)
#define TELEMETRY_PERIOD_MS 50      // 20 HZ (INVIO DATI A RASPBERRY)


/*
###########################################################################
# DEBUG                                                                   #
###########################################################################
*/
// #define DEBUG_MODE
#ifdef DEBUG_MODE
  #define DEBUG_PRINT(x)   Serial.print(x)
  #define DEBUG_PRINTLN(x) Serial.println(x)
#else
  #define DEBUG_PRINT(x)
  #define DEBUG_PRINTLN(x)
#endif