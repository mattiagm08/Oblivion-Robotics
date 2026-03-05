import time
from .baseState import BaseState
from config import MIN_SPEED

class SeesawNavigation(BaseState):
    """
    ###########################################################################
    # SEESAW NAVIGATION - STATE                                               #
    ###########################################################################
    # Gestisce l'attraversamento dell'altalena basculante senza usare pitch. #
    # Utilizza la rilevazione linea per capire quando il robot ha raggiunto  #
    # il fulcro e quando può terminare la discesa.                            #
    ###########################################################################
    """

    def __init__(self, stateMachine):
        super().__init__(stateMachine)
        self.phase      = "CLIMB"
        self.wait_start = 0

    def execute(self):
        data  = self.sm.lineCam.getLineData()

        if data is None or data['offset'] is None:
            return "GAP_CROSSING"

        offset = data['offset']
        lookAhead = data['lookAhead']

        # ##################################################################
        # FASE 1: SALITA VERSO IL FULCRO BASATA SULLA LINEA ALTA
        # ##################################################################
        if self.phase == "CLIMB":
            self.sm.logger.warn("Salita Seesaw...")
            self.sm.board.sendControl(offset, MIN_SPEED + 20)

            if lookAhead is not None:
                self.phase      = "WAIT"
                self.wait_start = time.time()
                self.sm.logger.info("Fulcro raggiunto. Attesa basculamento...")

        # ##################################################################
        # FASE 2: ATTESA BASCULAMENTO COMPLETO
        # ##################################################################
        elif self.phase == "WAIT":
            self.sm.board.sendControl(0, 0)
            if time.time() - self.wait_start > 1.5:
                self.phase = "DESCEND"
                self.sm.logger.success("Altalena abbassata. Procedo in discesa.")

        # ##################################################################
        # FASE 3: DISCESA CONTROLLATA
        # ##################################################################
        elif self.phase == "DESCEND":
            descent_speed = max(60, MIN_SPEED - 10)
            self.sm.board.sendControl(offset, descent_speed)

            if offset is not None and abs(offset) < 0.05:
                self.sm.logger.success("Seesaw completato.")
                self._reset()
                return "LINE_FOLLOW"

        return "SEESAW_NAVIGATION"

    def _reset(self):
        self.phase      = "CLIMB"
        self.wait_start = 0