from .baseState import BaseState
from config import MAX_SPEED, MIN_SPEED

class LineFollow(BaseState):
    """
    ###########################################################################
    # LINE FOLLOW - STATE                                                     #
    ###########################################################################
    # SEGUILINEA PURO CON VELOCITA' ADATTIVA (LOOK-AHEAD).                   #
    # NON CAMBIA MAI STATO: USATO PER TEST ISOLATO DEL SEGUILINEA.           #
    # - LINEA TROVATA:  CALCOLA OFFSET + VELOCITA' E INVIA ALL'ESP32.        #
    # - LINEA PERSA:    INVIA STOP (SPD:0) E ATTENDE IL RITORNO DELLA LINEA. #
    ###########################################################################
    # STERZO BASATO SULLA ROI ALTA (LOOK-AHEAD): IL ROBOT ANTICIPA LA CURVA  #
    # GUARDANDO LONTANO. LA ROI BASSA VIENE USATA SOLO PER LA VELOCITA'.     #
    ###########################################################################
    """

    def __init__(self, stateMachine):
        super().__init__(stateMachine)
        self.maxSpeed = MAX_SPEED
        self.minSpeed = MIN_SPEED

    def execute(self):

        # ##################################################################
        # ACQUISIZIONE DATI CAMERA                                         #
        # ##################################################################
        data = self.sm.lineCam.getLineData()

        # ##################################################################
        # LINEA NON TROVATA → STOP E ATTESA                                #
        # ##################################################################
        if data is None or data['offset'] is None:
            self.sm.board.sendControl(0.0, 0)
            return "LINE_FOLLOW"

        offsetLow  = data['offset']
        offsetHigh = data['lookAhead'] if data['lookAhead'] is not None else offsetLow

        # ##################################################################
        # STERZO: USA LA ROI ALTA PER ANTICIPARE LE CURVE                  #
        # ##################################################################
        steeringOffset = offsetHigh

        # ##################################################################
        # CALCOLO VELOCITA' DINAMICA (LOOK-AHEAD)                          #
        # PESO MAGGIORE AL LOOK-AHEAD (0.6) PER ANTICIPARE LE CURVE        #
        # ##################################################################
        curveFactor  = abs(offsetLow) * 0.4 + abs(offsetHigh) * 0.6
        speedRange   = self.maxSpeed - self.minSpeed
        currentSpeed = int(self.maxSpeed - curveFactor * speedRange)
        currentSpeed = max(self.minSpeed, currentSpeed)

        # ##################################################################
        # INVIO COMANDI ALLA MOTHERBOARD                                   #
        # ##################################################################
        self.sm.board.sendControl(steeringOffset, currentSpeed)

        return "LINE_FOLLOW"