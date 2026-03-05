import time
from .baseState import BaseState
from config import MIN_SPEED

class IntersectionHandling(BaseState):
    """
    ###########################################################################
    # INTERSECTION HANDLING - STATE                                           #
    ###########################################################################
    # GESTISCE I MARCATORI VERDI SUGLI INCROCI (ROBOCUP RESCUE LINE):         #
    #                                                                         #
    # - VERDE SINISTRA (greenLeft):   gira a sinistra                         #
    # - VERDE DESTRA  (greenRight):   gira a destra                           #
    # - DUE VERDI     (uTurn):        inversione ad U (dead end)              #
    #                                                                         #
    # FASI INTERNE:                                                           #
    #  1. ALIGN  → avanza brevemente per centrare l'asse ruote sull'incrocio  #
    #  2. TURN   → ruota sul posto nella direzione target                     #
    #  3. SEARCH → continua a ruotare finché non aggancia la nuova linea      #
    ###########################################################################
    # MAPPATURA ROBOCUP (immagine 2):                                         #
    #  greenLeft solo   → targetDir = LEFT                                    #
    #  greenRight solo  → targetDir = RIGHT                                   #
    #  greenLeft+Right  → targetDir = U_TURN (dead end)                       #
    #  nessun verde     → ritorno a LINE_FOLLOW (il robot va dritto)          #
    ###########################################################################
    """

    def __init__(self, stateMachine):
        super().__init__(stateMachine)
        self._reset()

    def execute(self):
        # ##################################################################
        # FASE 1: ACQUISIZIONE DATI CAMERA                                 #
        # ##################################################################
        data = self.sm.lineCam.getLineData()

        if data is None:
            return "GAP_CROSSING"

        # ##################################################################
        # FASE 2: ALIGN - CENTRAGGIO SULL'INCROCIO                         #
        # ##################################################################
        if self.phase == "ALIGN":

            # INIZIALIZZAZIONE TIMER E DIREZIONE TARGET (SOLO AL PRIMO CICLO)
            if self.startTime == 0:
                self.startTime = time.time()

                # MAPPATURA VERDE → DIREZIONE
                # uTurn ha priorità su greenLeft/greenRight (è la loro unione)
                if data['uTurn']:
                    self.targetDir = "U_TURN"
                elif data['greenLeft']:
                    self.targetDir = "LEFT"
                elif data['greenRight']:
                    self.targetDir = "RIGHT"
                else:
                    # NESSUN VERDE RILEVATO ALL'INGRESSO → TORNA AL FOLLOW
                    self._reset()
                    return "LINE_FOLLOW"

                self.sm.logger.warn(
                    f"INCROCIO RILEVATO: {self.targetDir}. ALLINEAMENTO IN CORSO..."
                )

            # AVANZAMENTO LINEARE PER PORTARE L'ASSE RUOTE SOPRA L'INCROCIO
            self.sm.board.sendControl(0, MIN_SPEED)

            # TRANSIZIONE ALLA ROTAZIONE DOPO 0.25s
            if time.time() - self.startTime > 0.25:
                self.phase = "TURN"
                self.startTime = time.time()   # RESET TIMER PER FASE TURN

            return "INTERSECTION_HANDLING"

        # ##################################################################
        # FASE 3: TURN - ROTAZIONE SUL POSTO                               #
        # ##################################################################
        elif self.phase == "TURN":

            if self.targetDir == "LEFT":
                self.sm.board.sendControl(-1.0, MIN_SPEED)
            elif self.targetDir == "RIGHT":
                self.sm.board.sendControl(1.0, MIN_SPEED)
            elif self.targetDir == "U_TURN":
                # U-TURN: rotazione a destra per ~180°
                # Il tempo esatto dipende dalla velocità dei motori; regolare in campo
                self.sm.board.sendControl(1.0, MIN_SPEED)

            # ATTESA MINIMA 0.4s PRIMA DI CERCARE LA NUOVA LINEA
            # (EVITA DI RILEVARE SUBITO IL VERDE / LA VECCHIA LINEA)
            if time.time() - self.startTime > 0.4:
                self.phase = "SEARCH"
                # FIX: startTime resettato qui per dare il corretto timeout di 3s
                # alla fase SEARCH (nel codice originale non veniva resettato,
                # causando un timeout quasi immediato se TURN durava > 3s)
                self.startTime = time.time()

            return "INTERSECTION_HANDLING"

        # ##################################################################
        # FASE 4: SEARCH - RICERCA NUOVA LINEA                             #
        # ##################################################################
        elif self.phase == "SEARCH":

            # LINEA AGGANCIATA: offset valido e abbastanza centrato
            if data['offset'] is not None and abs(data['offset']) < 0.6:
                self.sm.logger.success("LINEA AGGANCIATA! RIPRESA NAVIGAZIONE.")
                self._reset()
                return "LINE_FOLLOW"

            # CONTINUA ROTAZIONE NELLA STESSA DIREZIONE
            if self.targetDir == "LEFT":
                directionOffset = -1.0
            else:
                # RIGHT e U_TURN ruotano entrambi verso destra
                directionOffset = 1.0

            self.sm.board.sendControl(directionOffset, MIN_SPEED)

            # TIMEOUT DI SICUREZZA: 3s dalla fine della fase TURN
            if time.time() - self.startTime > 3.0:
                self.sm.logger.error(
                    "TIMEOUT SEARCH: linea non trovata. Passaggio a GAP_CROSSING."
                )
                self._reset()
                return "GAP_CROSSING"

            return "INTERSECTION_HANDLING"

        # FALLBACK (non dovrebbe mai accadere)
        self._reset()
        return "LINE_FOLLOW"

    # ######################################################################
    # RESET STATO                                                           #
    # ######################################################################
    def _reset(self):
        """Ripristina i parametri per l'incrocio successivo."""
        self.phase     = "ALIGN"
        self.targetDir = "NONE"
        self.startTime = 0