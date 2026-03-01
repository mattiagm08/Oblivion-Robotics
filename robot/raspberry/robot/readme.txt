robot/
│
├── main.py                         # Entry point, avvia FSM
├── config.py                       # Parametri modificabili (velocità, soglie, ecc.)
│
├── states/
│   ├── __init__.py
│   ├── baseState.py                # Classe astratta con execute() e transition()
│   ├── lineFollow.py               # Line following normale
│   ├── gapCrossing.py              # Attraversamento gap
│   ├── intersectionHandling.py     # Gestione incroci e dead end
│   ├── obstacleAvoidance.py        # Aggiramento ostacoli
│   ├── rampNavigation.py           # Salita/discesa rampe
│   ├── seesawNavigation.py         # Attraversamento seesaw
│   ├── evacuationZoneEnter.py      # Rilevamento nastro argento, ingresso EZ
│   ├── victimSearch.py             # Ricerca vittime nella EZ
│   ├── victimPickup.py             # Raccolta vittima
│   ├── victimDelivery.py           # Consegna vittima al triangolo corretto
│   ├── evacuationZoneExit.py       # Rilevamento nastro nero, uscita EZ
│   └── goalReached.py              # Stop 5 secondi sul goal tile
│
├── sensors/
│   ├── __init__.py
│   ├── lineCamera.py               # CV2: rileva linea, offset, gap, marker verdi
│   ├── colorDetector.py            # CV2: rileva nastro argento/nero/rosso/triangoli
│   └── victimDetector.py           # CV2: rileva e classifica vittime (argento/nere)
│
├── hardware/
│   ├── __init__.py
│   └── boardComm.py                # Seriale con ESP32: send/receive, parser protocollo
│
├── stateMachine.py                 # FSM: gestisce stati, transizioni, stato corrente
│
└── utils/
    ├── __init__.py
    ├── timer.py                    # Timer non-bloccanti
    └── logger.py                   # Log a schermo e su file
