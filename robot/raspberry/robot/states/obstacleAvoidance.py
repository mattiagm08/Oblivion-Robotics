import time
from .baseState import BaseState
from config import MIN_SPEED, OBSTACLE_DISTANCE


class ObstacleAvoidance(BaseState):
    """
    ###########################################################################
    # OBSTACLE AVOIDANCE - STATE                                              #
    ###########################################################################
    # Esegue una manovra di aggiramento quando il sensore ToF rileva          #
    # un ostacolo sulla linea.                                                #
    # La manovra è strutturata in fasi sequenziali temporizzate.              #
    ###########################################################################
    """

    def __init__(self, stateMachine):
        super().__init__(stateMachine)

        # FASE CORRENTE DELLA MANOVRA
        self.phase = "START_STOP"

        # TIMESTAMP DI RIFERIMENTO PER TRANSIZIONI TEMPORIZZATE
        self.start_time = 0

    def execute(self):

        # LETTURA DISTANZA DAL SENSORE TOF TRAMITE BOARD
        dist = self.sm.board.getDistance()

        # ##################################################################
        # FASE 1: ARRESTO INIZIALE                                         #
        # ##################################################################
        if self.phase == "START_STOP":

            # ARRESTO IMMEDIATO PER STABILIZZARE INERZIA E TRAIETTORIA
            self.sm.logger.warn("Ostacolo rilevato! Avvio manovra...")
            self.sm.board.sendControl(0, 0)

            # SALVATAGGIO TEMPO DI INIZIO MANOVRA
            self.start_time = time.time()
            self.phase = "TURN_OUT"

            return "OBSTACLE_AVOIDANCE"

        # ##################################################################
        # FASE 2: USCITA DALLA LINEA (Rotazione ~90°)                      #
        # ##################################################################
        elif self.phase == "TURN_OUT":

            # ROTAZIONE A SINISTRA CON OFFSET MASSIMO NEGATIVO
            self.sm.board.sendControl(-1.0, MIN_SPEED)

            # TRANSIZIONE DOPO TEMPO STIMATO PER ROTAZIONE DI 90°
            if time.time() - self.start_time > 0.6:
                self.phase = "ARC_AROUND"
                self.start_time = time.time()

            return "OBSTACLE_AVOIDANCE"

        # ##################################################################
        # FASE 3: ARCO DI AGGIRAMENTO                                      #
        # ##################################################################
        elif self.phase == "ARC_AROUND":

            # CURVA AMPIA A DESTRA PER SUPERARE L'INGOMBRO DELL'OSTACOLO
            # OFFSET POSITIVO MODERATO PER TRAIETTORIA CIRCOLARE STABILE
            self.sm.board.sendControl(0.6, MIN_SPEED + 20)

            # DURATA SUFFICIENTE A SUPERARE COMPLETAMENTE L'OGGETTO
            if time.time() - self.start_time > 2.5:
                self.phase = "SEARCH_LINE"

            return "OBSTACLE_AVOIDANCE"

        # ##################################################################
        # FASE 4: RICERCA LINEA                                            #
        # ##################################################################
        elif self.phase == "SEARCH_LINE":

            # ATTIVAZIONE MODALITÀ RICERCA LINEA
            self.sm.logger.info("Ricerca linea post-ostacolo...")

            data = self.sm.lineCam.getLineData()

            # SE LA LINEA VIENE RILEVATA NUOVAMENTE
            if data and data['offset'] is not None:
                self.sm.logger.success("Linea ritrovata! Ripresa navigazione.")
                self._reset()
                return "LINE_FOLLOW"

            # CONTINUA CURVA DI RIENTRO VERSO LA LINEA
            self.sm.board.sendControl(0.8, MIN_SPEED)

            return "OBSTACLE_AVOIDANCE"

    def _reset(self):

        # RIPRISTINO VARIABILI PER FUTURA ATTIVAZIONE STATO
        self.phase = "START_STOP"
        self.start_time = 0