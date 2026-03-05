import time
from .baseState import BaseState
from config import MIN_SPEED


class EvacuationZoneEnter(BaseState):
    """
    ###########################################################################
    # EVACUATION ZONE ENTER - STATE                                           #
    ###########################################################################
    # Gestisce l'ingresso nella zona di salvataggio.                          #
    #                                                                         #
    # Fasi Operative:                                                         #
    # 1. DETECT  => CONFERMA NASTRO ARGENTO (camera + sensore fisico ESP32)   #
    # 2. CROSS   => AVANZAMENTO OLTRE IL NASTRO E LA PARETE DI INGRESSO       #
    # 3. TRANSIT => ATTIVAZIONE MODALITÀ RICERCA VITTIME                      #
    ###########################################################################
    # REGOLA 3.9.4: nastro argento 25mm × 250mm all'ingresso EZ.              #
    # Il rilevamento visivo usa data['silver'] calcolato da LineCamera        #
    # tramite maschera HSV (nessun ColorDetector esterno necessario).         #
    ###########################################################################
    """

    def __init__(self, stateMachine):
        super().__init__(stateMachine)

        self.phase       = "DETECT"
        self.cross_start = 0

    def execute(self):

        data = self.sm.lineCam.getLineData()

        # ##################################################################
        # FASE 1: CONFERMA ARGENTO                                         #
        # ##################################################################
        if self.phase == "DETECT":

            self.sm.logger.warn("Conferma Nastro Argento in corso...")

            # Rilevamento SOLO visivo: il protocollo ESP32 non include campo argento.
            # data['silver'] e' calcolato da LineCamera tramite maschera HSV.
            silver_visual = data['silver'] if data else False

            if silver_visual:
                self.sm.logger.success("Nastro Argento confermato (VISIVO)! Ingresso EZ...")
                self.phase       = "CROSS"
                self.cross_start = time.time()

            # SEGUILINEA LENTO FINCHÉ NON SIAMO SOPRA IL NASTRO
            offset = data['offset'] if data and data['offset'] is not None else 0
            self.sm.board.sendControl(offset, MIN_SPEED)

        # ##################################################################
        # FASE 2: ATTRAVERSAMENTO NASTRO + PARETE DI INGRESSO              #
        # ##################################################################
        elif self.phase == "CROSS":

            self.sm.board.sendControl(0, MIN_SPEED)

            # AVANZA 1.5s PER ENTRARE COMPLETAMENTE NELL'EZ
            if time.time() - self.cross_start > 1.5:
                self.phase = "TRANSIT"

        # ##################################################################
        # FASE 3: TRANSIZIONE A RICERCA VITTIME                            #
        # ##################################################################
        elif self.phase == "TRANSIT":

            self.sm.logger.state("AREA EVACUAZIONE RAGGIUNTA")
            self.sm.board.sendControl(0, 0)
            self._reset()
            # FIX: era "RESCUE_SEARCH" che non esiste in stateMachine.
            #      Il nome corretto dalla struttura è "VICTIM_SEARCH".
            return "VICTIM_SEARCH"

        return "EVACUATION_ZONE_ENTER"

    def _reset(self):
        self.phase       = "DETECT"
        self.cross_start = 0