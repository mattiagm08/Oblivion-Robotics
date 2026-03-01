# Oblivion Robotics - Rescue Line 2026

Official repository for the **Oblivion Robotics** team participating in the **RoboCup Junior Rescue Line** competition. This project features a hybrid architecture designed for high-speed line following, advanced computer vision, and robust obstacle management.

## 🤖 System Architecture

Our robot utilizes a hybrid control system to balance high-level processing with real-time hardware response:

* **Brain (High-Level):** Raspberry Pi 5. Handles Computer Vision (OpenCV), Finite State Machine (FSM), and strategic decision-making.
* **Heart (Low-Level):** ESP32. Manages PID motor control, Time-of-Flight (ToF) distance sensors, IMU (Inertial Measurement Unit) data, and specialized hardware triggers.
* **Communication:** Custom asynchronous Serial Protocol (UART) over USB.
