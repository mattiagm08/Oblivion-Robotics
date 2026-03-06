import time
from .baseState import BaseState
from config import MIN_SPEED

class IntersectionHandling(BaseState):
    """Gestione marker verdi incroci RoboCup Rescue Line"""

    def __init__(self, stateMachine):
        super().__init__(stateMachine)
        self._reset()

    def execute(self):
        data = self.sm.lineCam.getLineData()
        if data is None:
            return "GAP_CROSSING"

        # ── ALIGN ──
        if self.phase == "ALIGN":
            if self.startTime == 0:
                self.startTime = time.time()
                if data.get('uTurn'):
                    self.targetDir = "U_TURN"
                elif data.get('greenLeft'):
                    self.targetDir = "LEFT"
                elif data.get('greenRight'):
                    self.targetDir = "RIGHT"
                else:
                    self._reset()
                    return "LINE_FOLLOW"

                self.sm.logger.warn(f"INCROCIO RILEVATO: {self.targetDir}. ALLINEAMENTO IN CORSO...")

            self.sm.board.sendControl(0, MIN_SPEED)

            if time.time() - self.startTime > 0.25:
                self.phase = "TURN"
                self.startTime = time.time()

            return "INTERSECTION_HANDLING"

        # ── TURN ──
        elif self.phase == "TURN":
            if self.targetDir == "LEFT":
                self.sm.board.sendControl(-1.0, MIN_SPEED)
            elif self.targetDir == "RIGHT":
                self.sm.board.sendControl(1.0, MIN_SPEED)
            elif self.targetDir == "U_TURN":
                self.sm.board.sendControl(1.0, MIN_SPEED)

            if time.time() - self.startTime > 0.4:
                self.phase = "SEARCH"
                self.startTime = time.time()

            return "INTERSECTION_HANDLING"

        # ── SEARCH ──
        elif self.phase == "SEARCH":
            if data.get('offset') is not None and abs(data['offset']) < 0.6:
                self.sm.logger.success("LINEA AGGANCIATA! RIPRESA NAVIGAZIONE.")
                self._reset()
                return "LINE_FOLLOW"

            directionOffset = -1.0 if self.targetDir == "LEFT" else 1.0
            self.sm.board.sendControl(directionOffset, MIN_SPEED)

            if time.time() - self.startTime > 3.0:
                self.sm.logger.error("TIMEOUT SEARCH: linea non trovata. Passaggio a GAP_CROSSING.")
                self._reset()
                return "GAP_CROSSING"

            return "INTERSECTION_HANDLING"

        self._reset()
        return "LINE_FOLLOW"

    def _reset(self):
        self.phase     = "ALIGN"
        self.targetDir = "NONE"
        self.startTime = 0