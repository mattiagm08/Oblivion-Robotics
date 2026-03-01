from .baseState import BaseState
from config import MAX_SPEED, MIN_SPEED, OBSTACLE_DISTANCE

class LineFollow(BaseState):
    """
    ###########################################################################
    # LINE FOLLOW - STATE                                                     #
    ###########################################################################
    # Gestisce il seguilinea principale con velocità adattiva (Look-Ahead).   #
    # Monitora costantemente i sensori per attivare le transizioni verso:     #
    # - OBSTACLE_AVOIDANCE: Se il ToF rileva un oggetto (Priorità 1).         #
    # - SEESAW_NAVIGATION: Se rileva inclinazione > 15°.                      #
    # - RAMP_NAVIGATION: Se rileva inclinazione tra 10° e 15°.                #
    # - GAP_CROSSING: Se la linea sparisce (ROI bassa vuota).                 #
    # - INTERSECTION_HANDLING: Se rileva marcatori verdi.                     #
    ###########################################################################
    """

    def __init__(self, stateMachine):
        super().__init__(stateMachine)
        self.maxSpeed = MAX_SPEED
        self.minSpeed = MIN_SPEED

    def execute(self):

        # ##################################################################
        # FASE 1: ACQUISIZIONE DATI SENSORI                                #
        # ##################################################################
        data = self.sm.lineCam.getLineData()
        distance = self.sm.board.getDistance()
        pitch = self.sm.board.getPitch()
        silver_physical = self.sm.board.getIsSilver()
        
        if data is None:
            return "GAP_CROSSING"

        # ##################################################################
        # FASE 2: PRIORITÀ MASSIMA - OSTACOLI                              #
        # ##################################################################
        if distance < OBSTACLE_DISTANCE:
            return "OBSTACLE_AVOIDANCE"

        # ##################################################################
        # FASE 3: RILEVAMENTO ARGENTO (RIDONDANZA BOARD + CAMERA)          #
        # ##################################################################
        silver_visual = self.sm.colorDet.checkForSilver(data['frame'])
        
        if silver_physical or silver_visual:
            source = "FISICO" if silver_physical else "VISIVO"
            self.sm.logger.warn(f"ARGENTO RILEVATO ({source})! INGRESSO EVACUATION ZONE")
            return "EVACUATION_ZONE_ENTER"

        # ##################################################################
        # FASE 4: CONTROLLO PENDENZE E RAMPE                               #
        # ##################################################################
        if abs(pitch) > 15.0:
            return "SEESAW_NAVIGATION"
        elif abs(pitch) > 10.0:
            return "RAMP_NAVIGATION"

        # ##################################################################
        # FASE 5: RILEVAMENTO MARCATORI VERDI                              #
        # ##################################################################
        if data['green_left'] or data['green_right']:
            return "INTERSECTION_HANDLING"

        # ##################################################################
        # FASE 6: GESTIONE LINEA PERSA / GAP                               #
        # ##################################################################
        if data['offset'] is None:
            return "GAP_CROSSING"

        # ##################################################################
        # FASE 7: CALCOLO VELOCITÀ DINAMICA (LOOK-AHEAD)                   #
        # ##################################################################
        look_ahead = data['look_ahead'] if data['look_ahead'] is not None else data['offset']

        # MIX PRECISIONE IMMEDIATA (OFFSET) E PREVISIONE (LOOK AHEAD)
        curve_factor = (abs(data['offset']) * 0.4) + (abs(look_ahead) * 0.6)

        speed_range = self.maxSpeed - self.minSpeed
        currentSpeed = int(self.maxSpeed - (curve_factor * speed_range))
        currentSpeed = max(self.minSpeed, currentSpeed)

        # ##################################################################
        # FASE 8: INVIO COMANDI ALLA BOARD                                 #
        # ##################################################################
        self.sm.board.sendControl(data['offset'], currentSpeed)

        return "LINE_FOLLOW"