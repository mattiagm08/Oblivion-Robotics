import time
from .baseState import BaseState
from config import MIN_SPEED


class SeesawNavigation(BaseState):
    """
    ###########################################################################
    # SEESAW NAVIGATION - STATE                                               #
    ###########################################################################
    # Gestisce l'attraversamento dell'altalena basculante.                    #
    #                                                                         #
    # Fasi Operative:                                                         #
    # 1. CLIMB   => SALITA FINO AL FULCRO (PITCH POSITIVO)                    #
    # 2. WAIT    => ARRESTO CENTRALE DURANTE BASCULAMENTO                     #
    # 3. DESCEND => DISCESA CONTROLLATA FINO A RIPRISTINO ORIZZONTALE         #
    ###########################################################################
    """

    def __init__(self, stateMachine):
        super().__init__(stateMachine)

        # FASE CORRENTE DELLA MACCHINA A STATI INTERNA
        self.phase = "CLIMB"

        # TIMESTAMP DI INIZIO ATTESA AL FULCRO
        self.wait_start = 0

        # MEMORIZZAZIONE ULTIMO VALORE DI PITCH PER RILEVAMENTO BASCULAMENTO
        self.last_pitch = 0

    def execute(self):

        # LETTURA INCLINAZIONE LONGITUDINALE DAL MICROCONTROLLORE
        pitch = self.sm.board.getPitch()

        # ACQUISIZIONE DATI LINEA DALLA VISIONE
        data = self.sm.lineCam.getLineData()

        # SE LA LINEA VIENE PERSA (FREQUENTE IN ZONA FULCRO)
        # TRANSIZIONE IMMEDIATA A GESTIONE GAP
        if data is None or data['offset'] is None:
            return "GAP_CROSSING"

        offset = data['offset']

        # ##################################################################
        # FASE 1: SALITA VERSO IL FULCRO                                   #
        # ##################################################################
        if self.phase == "CLIMB":

            # AVANZAMENTO LENTO E STABILE DURANTE LA SALITA
            self.sm.logger.warn(f"Salita Seesaw... Pitch: {pitch}")
            self.sm.board.sendControl(offset, MIN_SPEED + 20)

            # RILEVAMENTO SUPERAMENTO FULCRO
            # CONDIZIONE: CALO BRUSCO DEL PITCH RISPETTO AL FRAME PRECEDENTE
            if pitch < self.last_pitch - 5.0:
                self.phase = "WAIT"
                self.wait_start = time.time()
                self.sm.logger.info("Fulcro raggiunto. Attesa basculamento...")

        # ##################################################################
        # FASE 2: ATTESA BASCULAMENTO COMPLETO                             #
        # ##################################################################
        elif self.phase == "WAIT":

            # ARRESTO COMPLETO PER STABILIZZAZIONE STRUTTURA
            self.sm.board.sendControl(0, 0)

            # ATTESA TEMPORIZZATA PER CONSENTIRE CONTATTO LATO OPPOSTO
            if time.time() - self.wait_start > 1.5:
                self.phase = "DESCEND"
                self.sm.logger.success("Altalena abbassata. Procedo.")

        # ##################################################################
        # FASE 3: DISCESA CONTROLLATA                                      #
        # ##################################################################
        elif self.phase == "DESCEND":

            # DISCESA A VELOCITÀ RIDOTTA PER EVITARE IMPATTI
            self.sm.board.sendControl(offset, MIN_SPEED - 10)

            # CONDIZIONE DI USCITA: RIPRISTINO ORIZZONTALITÀ
            if abs(pitch) < 3.0:
                self.sm.logger.success("Seesaw completato.")
                self._reset()
                return "LINE_FOLLOW"

        # AGGIORNAMENTO VALORE PITCH PER FRAME SUCCESSIVO
        self.last_pitch = pitch

        return "SEESAW_NAVIGATION"

    def _reset(self):

        # RIPRISTINO STATO INTERNO PER FUTURE ATTIVAZIONI
        self.phase = "CLIMB"
        self.wait_start = 0