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
    # 1. DETECT  => IDENTIFICAZIONE NASTRO ARGENTO (FISICA + VISIVA)          #
    # 2. CROSS   => AVANZAMENTO CONTROLLATO OLTRE IL NASTRO                   #
    # 3. TRANSIT => ATTIVAZIONE MODALITÀ RICERCA VITTIME                      #
    ###########################################################################
    """

    def __init__(self, stateMachine):
        super().__init__(stateMachine)

        # FASE CORRENTE DELLA PROCEDURA DI INGRESSO
        self.phase = "DETECT"

        # TIMESTAMP PER IL CONTROLLO DELL'AVANZAMENTO OLTRE IL NASTRO
        self.cross_start = 0

    def execute(self):

        # ACQUISIZIONE DATI SENSORI E VISIONE
        data = self.sm.lineCam.getLineData()
        silver_physical = self.sm.board.getIsSilver()

        # ##################################################################
        # FASE 1: CONFERMA ARGENTO                                         #
        # ##################################################################
        if self.phase == "DETECT":

            self.sm.logger.warn("Conferma Nastro Argento in corso...")
            
            # RIDONDANZA: CONTROLLO SIA IL FLAG DELLA CAMERA SIA IL SENSORE SULL'ESP32
            silver_visual = self.sm.colorDet.checkForSilver(data['frame']) if data else False
            
            if silver_physical or silver_visual:
                source = "FISICO" if silver_physical else "VISIVO"
                self.sm.logger.success(f"Nastro Argento confermato ({source})! Ingresso...")
                self.phase = "CROSS"
                self.cross_start = time.time()
            
            # MANTENIMENTO SEGUILINEA LENTO FINCHÉ NON SIAMO SOPRA IL NASTRO
            offset = data['offset'] if data and data['offset'] is not None else 0
            self.sm.board.sendControl(offset, MIN_SPEED)

        # ##################################################################
        # FASE 2: ATTRAVERSAMENTO NASTRO                                   #
        # ##################################################################
        elif self.phase == "CROSS":

            # AVANZAMENTO DRITTO PER SUPERARE IL NASTRO E LA PARETE DI INGRESSO
            self.sm.board.sendControl(0, MIN_SPEED)

            # IL ROBOT AVANZA PER 1.5 SECONDI PER ENTRARE COMPLETAMENTE NELL'AREA
            if time.time() - self.cross_start > 1.5:
                self.phase = "TRANSIT"

        # ##################################################################
        # FASE 3: TRANSIZIONE A RICERCA VITTIME                            #
        # ##################################################################
        elif self.phase == "TRANSIT":

            self.sm.logger.state("AREA EVACUAZIONE RAGGIUNTA")
            
            # FERMIAMO IL ROBOT PRIMA DI CAMBIARE MODALITÀ
            self.sm.board.sendControl(0, 0)
            
            self._reset()
            return "RESCUE_SEARCH"

        return "EVACUATION_ZONE_ENTER"

    def _reset(self):
        """ RIPRISTINO STATO INTERNO PER UTILIZZI FUTURI """
        self.phase = "DETECT"
        self.cross_start = 0