# Firmware Structure

firmware/
│
├── main.cpp # Setup + main loop
├── config.h # Hardware constants (pins, max speed, etc.)
│
├── comm/
│ ├── serialProtocol.h
│ └── serialProtocol.cpp # Command parser from Raspberry Pi, response formatting
│
├── motor/
│ ├── motorDriver.h
│ ├── motorDriver.cpp # Left/Right motor PWM and direction control
│ ├── pidController.h
│ ├── pidController.cpp # Reusable generic PID controller
│ ├── encoder.h
│ └── encoder.cpp # Encoder reading, speed and distance calculation
│
├── sensors/
│ ├── tofSensor.h
│ ├── tofSensor.cpp # VL53L0X or similar, obstacle/victim distance
│ ├── imuSensor.h
│ ├── imuSensor.cpp # MPU6050 or similar, heading and tilt
│ ├── colorSensor.h
│ └── colorSensor.cpp # TCS34725 or similar, victim surface detection
│
└── actuators/
├── rescueArm.h
└── rescueArm.cpp # Arm servo/motor, open/close control