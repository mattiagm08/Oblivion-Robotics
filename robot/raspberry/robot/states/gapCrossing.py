import time
from .baseState import BaseState
from config import GAP_SPEED, GAP_TIMEOUT


class GapCrossing(BaseState):
    """
    ###########################################################################
    # GAP CROSSING - STATE                                                    #
    ###########################################################################
    # Gestisce il caso in cui la linea nera viene persa (gap sul percorso).  #
    # Il robot avanza in linea retta all'ultima velocità nota finché         #
    # la linea non viene ripresa o scatta il timeout.                        #
    ###########################################################################
    # REGOLA 3.3.2: gap max 20cm, almeno 5cm di linea prima del gap.         #
    # GAP_TIMEOUT e GAP_SPEED sono definiti in config.py per calibrazione    #
    # rapida senza toccare il codice.                                        #
    ###########################################################################
    """

    def __init__(self, stateMachine):
        super().__init__(stateMachine)
        self.entryTime = 0
        self.timeout   = GAP_TIMEOUT

    def execute(self):

        # ##################################################################
        # FASE 1: INIZIALIZZAZIONE (primo ciclo nello stato)               #
        # ##################################################################
        if self.entryTime == 0:
            self.entryTime = time.time()
            self.sm.logger.warn("LINEA PERSA! AVVIO PROCEDURA GAP CROSSING...")

        # ##################################################################
        # FASE 2: VERIFICA SE LA LINEA È RIPRESA                           #
        # ##################################################################
        data = self.sm.lineCam.getLineData()
        if data and data['offset'] is not None:
            self.sm.logger.info("LINEA RITROVATA!")
            self.entryTime = 0
            return "LINE_FOLLOW"

        # ##################################################################
        # FASE 3: TIMEOUT - LINEA NON TROVATA                              #
        # ##################################################################
        if time.time() - self.entryTime > self.timeout:
            self.sm.logger.error("TIMEOUT GAP CROSSING! LINEA NON TROVATA.")
            self.sm.board.sendControl(0, 0)
            self.entryTime = 0
            return "LINE_FOLLOW"

        # ##################################################################
        # FASE 4: AVANZAMENTO RETTILINEO SUL GAP                           #
        # ##################################################################
        # FIX: era hardcoded 120 → usa GAP_SPEED da config.py
        self.sm.board.sendControl(0.0, GAP_SPEED)

        return "GAP_CROSSING"