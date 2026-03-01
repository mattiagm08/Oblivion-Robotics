firmware/
│
├── main.cpp                        # Setup + loop principale
├── config.h                        # Costanti hardware (pin, velocità max, ecc.)
│
├── comm/
│   ├── serialProtocol.h
│   └── serialProtocol.cpp          # Parser comandi da Rasp, formattazione risposte
│
├── motor/
│   ├── motorDriver.h
│   ├── motorDriver.cpp             # PWM motori L/R, direzione
│   ├── pidController.h
│   ├── pidController.cpp           # PID generico riusabile
│   ├── encoder.h
│   └── encoder.cpp                 # Lettura encoder, calcolo velocità/distanza
│
├── sensors/
│   ├── tofSensor.h
│   ├── tofSensor.cpp               # VL53L0X o simile, distanza ostacoli/vittime
│   ├── imuSensor.h
│   ├── imuSensor.cpp               # MPU6050 o simile, heading, inclinazione
│   ├── colorSensor.h
│   └── colorSensor.cpp             # TCS34725 o simile, conduttività vittima
│
└── actuators/
    ├── rescueArm.h
    └── rescueArm.cpp               # Servo/motore braccio, apertura/chiusura