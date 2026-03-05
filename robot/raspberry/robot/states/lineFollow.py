from .baseState import BaseState
from config import MAX_SPEED, MIN_SPEED, GAP_SPEED, BACK_SPEED, GAP_TIMEOUT
import time

class LineFollow(BaseState):
    """
    ###########################################################################
    # LINE FOLLOW - STATE                                                     #
    ###########################################################################
    # SEGUILINEA CON VELOCITA' ADATTIVA (LOOK-AHEAD) E RECUPERO LINEA         #
    # - LINEA TROVATA: CALCOLA OFFSET + VELOCITA' E INVIA ALL'ESP32           #
    # - LINEA PERSA: AVANZA POCO (GAP), SE ANCORA PERSA TORNA INDIETRO        #
    ###########################################################################
    """

    def __init__(self, stateMachine):
        super().__init__(stateMachine)
        self.maxSpeed = MAX_SPEED
        self.minSpeed = MIN_SPEED
        self.lostLineTime = 0
        self.backwardPhase = False

    def execute(self):

        # ##################################################################
        # ACQUISIZIONE DATI CAMERA                                         #
        # ##################################################################
        data = self.sm.lineCam.getLineData()

        # ##################################################################
        # LINEA TROVATA                                                    #
        # ##################################################################
        if data and data['offset'] is not None:
            self.lostLineTime = 0
            self.backwardPhase = False

            offsetLow  = data['offset']
            offsetHigh = data['lookAhead'] if data['lookAhead'] is not None else offsetLow

            # STERZO
            steeringOffset = offsetHigh

            # VELOCITA' DINAMICA
            curveFactor  = abs(offsetLow) * 0.4 + abs(offsetHigh) * 0.6
            speedRange   = self.maxSpeed - self.minSpeed
            currentSpeed = int(self.maxSpeed - curveFactor * speedRange)
            currentSpeed = max(self.minSpeed, currentSpeed)

            self.sm.board.sendControl(steeringOffset, currentSpeed)
            return "LINE_FOLLOW"

        # ##################################################################
        # LINEA PERSA                                                     #
        # ##################################################################
        currentTime = time.time()

        if self.lostLineTime == 0:
            self.lostLineTime = currentTime
            self.backwardPhase = False
            self.sm.logger.warn("LINEA PERSA! AVANZAMENTO PER GAP...")

        elapsed = currentTime - self.lostLineTime

        # PRIMA FASE: AVANZA PER GAP_TIMEOUT / 2
        if not self.backwardPhase and elapsed <= GAP_TIMEOUT / 2:
            self.sm.board.sendControl(0.0, GAP_SPEED)
            return "LINE_FOLLOW"

        # SE ANCORA NON TROVA LINEA → TORNA INDIETRO
        if not self.backwardPhase:
            self.backwardPhase = True
            self.lostLineTime = currentTime
            self.sm.logger.warn("LINEA ANCORA NON TROVATA! RITORNO INDIETRO...")
            self.sm.board.sendControl(0.0, -BACK_SPEED)
            return "LINE_FOLLOW"

        # FASE INDIETRO: se timeout → stop
        if self.backwardPhase and elapsed > GAP_TIMEOUT / 2:
            self.sm.logger.error("LINEA PERSA DOPO INDIETRO! STOP")
            self.sm.board.sendControl(0.0, 0)
            self.lostLineTime = 0
            self.backwardPhase = False
            return "LINE_FOLLOW"

        # CONTINUA A TORNARE INDIETRO
        self.sm.board.sendControl(0.0, -BACK_SPEED)
        return "LINE_FOLLOW"