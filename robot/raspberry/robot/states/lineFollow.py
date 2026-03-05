from .baseState import BaseState
from config import MAX_SPEED, MIN_SPEED, OBSTACLE_DISTANCE

class LineFollow(BaseState):
    """
    ###########################################################################
    # LINE FOLLOW - STATE                                                     #
    ###########################################################################
    # GESTISCE IL SEGUILINEA PRINCIPALE CON VELOCITA' ADATTIVA (LOOK-AHEAD). #
    # MONITORA COSTANTEMENTE I SENSORI PER ATTIVARE LE TRANSIZIONI VERSO:    #
    # - OBSTACLE_AVOIDANCE:    SE IL TOF RILEVA UN OGGETTO (PRIORITA' 1).    #
    # - EVACUATION_ZONE_ENTER: SE RILEVA IL NASTRO ARGENTO (via LineCamera). #
    # - INTERSECTION_HANDLING: SE RILEVA MARCATORI VERDI (INCROCIO/U-TURN).  #
    # - GAP_CROSSING:          SE LA LINEA SPARISCE (OFFSET NULLO).          #
    ###########################################################################
    # LOGICA VERDI (ROBOCUP RESCUE LINE):                                     #
    # - uTurn (verde SX + DX):  -> INTERSECTION_HANDLING (targetDir=U_TURN)  #
    # - greenLeft:              -> INTERSECTION_HANDLING (targetDir=LEFT)     #
    # - greenRight:             -> INTERSECTION_HANDLING (targetDir=RIGHT)    #
    # - greenForward (solo):    -> nessuna transizione, prosegue dritto       #
    ###########################################################################
    """

    def __init__(self, stateMachine):
        super().__init__(stateMachine)
        self.maxSpeed = MAX_SPEED
        self.minSpeed = MIN_SPEED

    def execute(self):

        # ##################################################################
        # FASE 1: ACQUISIZIONE DATI SENSORI E CAMERA                       #
        # ##################################################################
        data          = self.sm.lineCam.getLineData()
        distanceFront = self.sm.board.getDistanceFront()
        distanceLeft  = self.sm.board.getDistanceLeft()
        distanceRight = self.sm.board.getDistanceRight()

        if data is None:
            return "GAP_CROSSING"

        # ##################################################################
        # FASE 2: PRIORITA' MASSIMA - OSTACOLI (TOF)                       #
        # ##################################################################
        if (distanceFront < OBSTACLE_DISTANCE or
            distanceLeft  < OBSTACLE_DISTANCE or
            distanceRight < OBSTACLE_DISTANCE):
            return "OBSTACLE_AVOIDANCE"

        # ##################################################################
        # FASE 3: RILEVAMENTO ARGENTO (INGRESSO EVACUATION ZONE)           #
        # ##################################################################
        if data['silver']:
            self.sm.logger.warn("ARGENTO RILEVATO! INGRESSO EVACUATION ZONE")
            return "EVACUATION_ZONE_ENTER"

        # ##################################################################
        # FASE 5: RILEVAMENTO MARCATORI VERDI (ROBOCUP RESCUE LINE)        #
        # ##################################################################
        if data['uTurn']:
            return "INTERSECTION_HANDLING"

        if data['greenLeft'] or data['greenRight']:
            return "INTERSECTION_HANDLING"

        # ##################################################################
        # FASE 6: GESTIONE LINEA PERSA / GAP                               #
        # ##################################################################
        if data['offset'] is None:
            return "GAP_CROSSING"

        # ##################################################################
        # FASE 7: CALCOLO VELOCITA' DINAMICA (LOOK-AHEAD)                  #
        # ##################################################################
        lookAheadVal = data['lookAhead'] if data['lookAhead'] is not None else data['offset']

        # Peso maggiore al look-ahead (0.6) per anticipare le curve
        curveFactor  = (abs(data['offset']) * 0.4) + (abs(lookAheadVal) * 0.6)

        speedRange   = self.maxSpeed - self.minSpeed
        currentSpeed = int(self.maxSpeed - (curveFactor * speedRange))
        currentSpeed = max(self.minSpeed, currentSpeed)

        # ##################################################################
        # FASE 8: INVIO COMANDI ALLA MOTHERBOARD                           #
        # ##################################################################
        self.sm.board.sendControl(data['offset'], currentSpeed)

        return "LINE_FOLLOW"