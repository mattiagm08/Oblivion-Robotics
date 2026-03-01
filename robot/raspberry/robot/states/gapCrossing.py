import time
from .baseState import BaseState

class GapCrossing(BaseState):
    """
    ###########################################################################
    # GAP CROSSING - STATE                                                    #
    ###########################################################################
    # Gestisce il caso in cui la linea nera viene persa.                      #
    # Il robot prosegue diritto mantenendo l'ultimo heading noto dall'IMU     #
    # fino a quando la linea non viene ripresa.                               #
    ###########################################################################
    """

    def __init__(self, stateMachine):
        super().__init__(stateMachine)
        self.entry_time = 0
        self.timeout = 2.5  # SE DOPO 2.5s NON TROVA LINEA, SI FERMA

    def execute(self):
        # ##################################################################
        # FASE 1: INIZIALIZZAZIONE GAP CROSSING                            #
        # ##################################################################
        if self.entry_time == 0:
            self.entry_time = time.time()
            self.sm.logger.warn("LINEA PERSA! AVVIO PROCEDURA GAP CROSSING...")

        # ##################################################################
        # FASE 2: VERIFICA SE LA LINEA È RIPRESA                           #
        # ##################################################################
        data = self.sm.lineCam.getLineData()
        if data and data['offset'] is not None:
            self.sm.logger.info("LINEA RITROVATA!")
            self.entry_time = 0  # RESET PER LA PROSSIMA VOLTA
            return "LINE_FOLLOW"

        # ##################################################################
        # FASE 3: CONTROLLO TIMEOUT                                        #
        # ##################################################################
        if time.time() - self.entry_time > self.timeout:
            self.sm.logger.error("TIMEOUT GAP CROSSING! LINEA NON TROVATA.")
            # FERMA IL ROBOT IN SICUREZZA
            self.sm.board.sendControl(0, 0)
            return "LINE_FOLLOW"  # O STATO DI ERRORE/RICERCA

        # ##################################################################
        # FASE 4: AZIONE - AVANZAMENTO LINEARE                             #
        # ##################################################################
        # VELOCITÀ RIDOTTA, OFFSET AZZERATO PER MANTENERE DIREZIONE RETTA
        # SI PUÒ UTILIZZARE L'HEADING DELL'IMU PER CORREZIONE FUTURA
        self.sm.board.sendControl(0.0, 120)

        # PERMANENZA NELLO STATO FINCHÉ NON SI VERIFICA UNA CONDIZIONE DI TRANSIZIONE
        return "GAP_CROSSING"