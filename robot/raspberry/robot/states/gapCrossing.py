import time
from .baseState import BaseState
from config import GAP_SPEED, GAP_TIMEOUT

class GapCrossing(BaseState):
    """
    Attraversa un gap (interruzione della linea) avanzando dritto.
    Torna in LINE_FOLLOW appena una qualsiasi ROI (FAR, MID o NEAR)
    rileva di nuovo la linea — grazie al farthest-point tracking di
    LineCamera, il rientro avviene prima rispetto alla versione precedente.
    """

    def __init__(self, stateMachine):
        super().__init__(stateMachine)
        self.entryTime = 0

    def execute(self):
        currentTime = time.time()

        if self.entryTime == 0:
            self.entryTime = currentTime
            self.sm.logger.warn("STATO: GAP CROSSING ATTIVO.")

        # CONTROLLO LINEA — offset è il punto più lontano visibile:
        # rientra prima perché la ROI FAR vede la linea dall'altro lato del gap
        # ancora prima che il robot ci sia sopra.
        data = self.sm.lineCam.getLineData()
        if data and data['offset'] is not None:
            self.sm.logger.info(
                f"GAP SUPERATO via ROI={data.get('activeRoi','?')} "
                f"offset={data['offset']:.2f}"
            )
            self.entryTime = 0
            return "LINE_FOLLOW"

        # TIMEOUT di sicurezza
        if currentTime - self.entryTime > GAP_TIMEOUT:
            self.sm.logger.error("GAP FALLITO! ARRESTO DI SICUREZZA.")
            self.sm.board.sendControl(0.0, 0)
            self.entryTime = 0
            return "LINE_FOLLOW"

        self.sm.board.sendControl(0.0, GAP_SPEED)
        return "GAP_CROSSING"