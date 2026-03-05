import time
from .baseState import BaseState
from config import GAP_SPEED, GAP_TIMEOUT

class GapCrossing(BaseState):
    """
    ###########################################################################
    # GAP CROSSING - STATE                                                    #
    ###########################################################################
    # Gestisce il caso in cui la linea nera viene persa (gap sul percorso).  #
    # Avanza in linea retta all'ultima velocità nota finché la linea non      #
    # viene ripresa o scatta il timeout.                                      #
    ###########################################################################
    """

    def __init__(self, stateMachine):
        super().__init__(stateMachine)
        self.entryTime = 0
        self.timeout   = GAP_TIMEOUT

    def execute(self):

        # INIZIALIZZAZIONE PRIMO CICLO
        if self.entryTime == 0:
            self.entryTime = time.time()
            self.sm.logger.warn("LINEA PERSA! AVVIO PROCEDURA GAP CROSSING...")

        # VERIFICA LINEA RIPRESA
        data = self.sm.lineCam.getLineData()
        if data and data['offset'] is not None:
            self.sm.logger.info("LINEA RITROVATA!")
            self.entryTime = 0
            return "LINE_FOLLOW"

        # TIMEOUT
        if time.time() - self.entryTime > self.timeout:
            self.sm.logger.error("TIMEOUT GAP CROSSING! LINEA NON TROVATA.")
            self.sm.board.sendControl(0, 0)
            self.entryTime = 0
            return "LINE_FOLLOW"

        # AVANZAMENTO RETTILINEO SUL GAP
        self.sm.board.sendControl(0.0, GAP_SPEED)
        return "GAP_CROSSING"