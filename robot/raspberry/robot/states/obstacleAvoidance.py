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
    # REGOLA 3.5.4: ostacoli alti almeno 15cm, possono essere fissi.         #
    # La manovra aggira a sinistra (TURN_OUT), poi arco a destra (ARC_AROUND) #
    # per tornare sulla linea dal lato opposto.                               #
    ###########################################################################
    """

    def __init__(self, stateMachine):
        super().__init__(stateMachine)
        self.phase      = "START_STOP"
        self.start_time = 0

    def execute(self):

        dist = self.sm.board.getDistanceFront()

        # ##################################################################
        # FASE 1: ARRESTO INIZIALE                                         #
        # ##################################################################
        if self.phase == "START_STOP":
            self.sm.logger.warn("Ostacolo rilevato! Avvio manovra...")
            self.sm.board.sendControl(0, 0)
            self.start_time = time.time()
            self.phase = "TURN_OUT"
            return "OBSTACLE_AVOIDANCE"

        # ##################################################################
        # FASE 2: USCITA DALLA LINEA (~90° a sinistra)                     #
        # ##################################################################
        elif self.phase == "TURN_OUT":
            self.sm.board.sendControl(-1.0, MIN_SPEED)
            if time.time() - self.start_time > 0.6:
                self.phase      = "ARC_AROUND"
                self.start_time = time.time()
            return "OBSTACLE_AVOIDANCE"

        # ##################################################################
        # FASE 3: ARCO DI AGGIRAMENTO                                      #
        # ##################################################################
        elif self.phase == "ARC_AROUND":
            self.sm.board.sendControl(0.6, MIN_SPEED + 20)
            if time.time() - self.start_time > 2.5:
                self.phase      = "SEARCH_LINE"
                self.start_time = time.time()  
            return "OBSTACLE_AVOIDANCE"

        # ##################################################################
        # FASE 4: RICERCA LINEA                                            #
        # ##################################################################
        elif self.phase == "SEARCH_LINE":
            self.sm.logger.info("Ricerca linea post-ostacolo...")
            data = self.sm.lineCam.getLineData()

            if data and data['offset'] is not None:
                self.sm.logger.success("Linea ritrovata! Ripresa navigazione.")
                self._reset()
                return "LINE_FOLLOW"

            if time.time() - self.start_time > 5.0:
                self.sm.logger.error(
                    "TIMEOUT ricerca linea post-ostacolo. Ritorno a LINE_FOLLOW."
                )
                self._reset()
                return "LINE_FOLLOW"

            if dist < OBSTACLE_DISTANCE:
                self.sm.board.sendControl(0, 0)
            else:
                self.sm.board.sendControl(0.8, MIN_SPEED)

            return "OBSTACLE_AVOIDANCE"

    def _reset(self):
        self.phase      = "START_STOP"
        self.start_time = 0