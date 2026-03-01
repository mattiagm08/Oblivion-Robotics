Robot Software Architecture

robot/
│
├── main.py # Entry point, starts the FSM
├── config.py # Adjustable parameters (speed, thresholds, etc.)
│
├── states/
│ ├── init.py
│ ├── baseState.py # Abstract class with execute() and transition()
│ ├── lineFollow.py # Standard line following
│ ├── gapCrossing.py # Gap crossing logic
│ ├── intersectionHandling.py # Intersections and dead-end handling
│ ├── obstacleAvoidance.py # Obstacle avoidance
│ ├── rampNavigation.py # Ramp ascent/descent handling
│ ├── seesawNavigation.py # Seesaw traversal
│ ├── evacuationZoneEnter.py # Silver tape detection, EZ entry
│ ├── victimSearch.py # Victim search inside the EZ
│ ├── victimPickup.py # Victim pickup logic
│ ├── victimDelivery.py # Deliver victim to the correct triangle
│ ├── evacuationZoneExit.py # Black tape detection, EZ exit
│ └── goalReached.py # Stop 5 seconds on the goal tile
│
├── sensors/
│ ├── init.py
│ ├── lineCamera.py # OpenCV: detects line, offset, gaps, green markers
│ ├── colorDetector.py # OpenCV: detects silver/black/red tape and triangles
│ └── victimDetector.py # OpenCV: detects and classifies victims (silver/black)
│
├── hardware/
│ ├── init.py
│ └── boardComm.py # Serial communication with ESP32: send/receive, protocol parsing
│
├── stateMachine.py # FSM: manages states, transitions, current state
│
└── utils/
├── init.py
├── timer.py # Non-blocking timers
└── logger.py # Console and file logging