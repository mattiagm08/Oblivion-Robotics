import time
from .baseState import BaseState
from config import MIN_SPEED

class IntersectionHandling(BaseState):
    """
    ###########################################################################
    # INTERSECTION HANDLING - STATE                                           #
    ###########################################################################
    # Gestisce i marcatori verdi sui incroci:                                 #
    # - VERDE A SINISTRA: Rotazione a sinistra                                #
    # - VERDE A DESTRA: Rotazione a destra                                    #
    # - DUE VERDI: Inversione ad U (180°)                                     #
    ###########################################################################
    """

    def __init__(self, stateMachine):
        super().__init__(stateMachine)

        # FASI: ALIGN, TURN, SEARCH
        self.phase = "ALIGN"
        self.target_dir = "NONE"
        self.start_time = 0

    def execute(self):
        # ##################################################################
        # FASE 1: ACQUISIZIONE DATI CAMERA                                 #
        # ##################################################################
        # RECUPERO DATI LINEA DALLA CAMERA PER RILEVARE OFFSET E VERDE
        data = self.sm.lineCam.getLineData()

        # ##################################################################
        # FASE 2: ALIGN - CENTRAGGIO SULL'INCROCIO                         #
        # ##################################################################
        if self.phase == "ALIGN":
            # INIZIALIZZAZIONE TIMER E DIREZIONE TARGET
            if self.start_time == 0:
                self.start_time = time.time()

                # DETERMINAZIONE DIREZIONE IN BASE AI MARCATORI VERDI
                if data['green_left'] and data['green_right']:
                    self.target_dir = "U_TURN"
                elif data['green_left']:
                    self.target_dir = "LEFT"
                elif data['green_right']:
                    self.target_dir = "RIGHT"

                self.sm.logger.warn(f"MARCATORE RILEVATO: {self.target_dir}. ALLINEAMENTO...")

            # AVANZAMENTO LINEARE PER 250ms PER CENTRARE L'ASSE RUOTE
            self.sm.board.sendControl(0, MIN_SPEED)

            # TRANSIZIONE ALLA FASE SUCCESSIVA DOPO TEMPO DI AVANZAMENTO
            if time.time() - self.start_time > 0.25:
                self.phase = "TURN"
                self.start_time = time.time()

            return "INTERSECTION_HANDLING"

        # ##################################################################
        # FASE 3: TURN - ROTAZIONE SUL POSTO                               #
        # ##################################################################
        elif self.phase == "TURN":
            self.sm.logger.info(f"ESECUZIONE ROTAZIONE: {self.target_dir}")

            # ESECUZIONE ROTAZIONE IN BASE ALLA DIREZIONE TARGET
            if self.target_dir == "LEFT":
                self.sm.board.sendControl(-1.0, MIN_SPEED)  # OFFSET -1 = ROTAZIONE SINISTRA
            elif self.target_dir == "RIGHT":
                self.sm.board.sendControl(1.0, MIN_SPEED)   # OFFSET 1 = ROTAZIONE DESTRA
            elif self.target_dir == "U_TURN":
                self.sm.board.sendControl(1.0, MIN_SPEED)   # ROTAZIONE FINO A 180°

            # ASPETTA UN TEMPO MINIMO PER USCIRE DALLA LINEA ATTUALE
            if time.time() - self.start_time > 0.4:
                self.phase = "SEARCH"

            return "INTERSECTION_HANDLING"

        # ##################################################################
        # FASE 4: SEARCH - RICERCA NUOVA LINEA                             #
        # ##################################################################
        elif self.phase == "SEARCH":
            # VERIFICA SE LA LINEA È RIPRESA (OFFSET VICINO A ZERO)
            if data and data['offset'] is not None and abs(data['offset']) < 0.5:
                self.sm.logger.success("LINEA AGGANCIATA DOPO INCROCIO!")
                self._reset()
                return "LINE_FOLLOW"

            # CONTINUA A GIRARE NELLA DIREZIONE SCELTA
            speed = MIN_SPEED
            offset = -1.0 if self.target_dir == "LEFT" else 1.0
            self.sm.board.sendControl(offset, speed)

            return "INTERSECTION_HANDLING"

    # ##################################################################
    # RESET STATO                                                      #
    # ##################################################################
    # RIPRISTINA I PARAMETRI PER L'INCROCIO SUCCESSIVO
    def _reset(self):
        self.phase = "ALIGN"
        self.target_dir = "NONE"
        self.start_time = 0