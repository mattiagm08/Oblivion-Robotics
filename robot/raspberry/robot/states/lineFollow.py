import time
from collections import deque
from .baseState import BaseState
from config import MAX_SPEED, MIN_SPEED

class LineFollow(BaseState):

    # ── Blind turn ────────────────────────────────────────────────────────────
    BLIND_TURN_OFFSET_THRESHOLD = 0.45
    MAX_BLIND_FRAMES            = 10
    BLIND_TURN_AMPLIFY          = 1.10

    # ── Speed clamp ───────────────────────────────────────────────────────────
    CURVE_SLOW_THRESHOLD    = 0.30
    CURVE_CONFIRM_THRESHOLD = 0.40
    CURVE_MIN_SPEED         = None
    CURVE_SPEED_EXPONENT    = 2.5

    # ── Shake ─────────────────────────────────────────────────────────────────
    SHAKE_REVERSE_SPEED = None
    MAX_SHAKE_DURATION  = 2.5
    SHAKE_INTERVAL      = 0.3

    def __init__(self, stateMachine):
        super().__init__(stateMachine)

        self.shakeActive      = False
        self.shakeStartTime   = 0
        self.initialShakeDir  = 1.0   # Sostituito shakeDirection con initialShakeDir per affidabilità
        self.lastValidOffset  = 0.0
        self.bufferSize       = 3
        self.commandQueue     = deque(maxlen=self.bufferSize)
        self.blindTurnFrames  = 0
        self.lastSeenDir      = 1
        self.shakeAmplitude   = MAX_SPEED

        if self.CURVE_MIN_SPEED is None:
            self.CURVE_MIN_SPEED = MIN_SPEED + 10
        if self.SHAKE_REVERSE_SPEED is None:
            self.SHAKE_REVERSE_SPEED = MIN_SPEED

        self.offsetFiltered = 0.0

    def _computeSpeed(self, offsetFar, offsetNear):
        speedRange  = MAX_SPEED - MIN_SPEED
        abs_offset = abs(offsetFar)

        # NOVITÀ: Zona morta per il rettilineo. Se l'errore è piccolissimo, vai al massimo.
        if abs_offset < 0.15:
            targetSpeed = MAX_SPEED
        else:
            targetSpeed = int(MAX_SPEED - speedRange * (abs_offset ** self.CURVE_SPEED_EXPONENT))
        
        targetSpeed = max(MIN_SPEED, targetSpeed)

        # Rallentamento drastico solo se la curva è decisa
        if abs_offset >= self.CURVE_SLOW_THRESHOLD:
            targetSpeed = min(targetSpeed, self.CURVE_MIN_SPEED)

        if offsetNear is not None and abs(offsetNear) >= self.CURVE_CONFIRM_THRESHOLD:
            targetSpeed = min(targetSpeed, self.CURVE_MIN_SPEED)

        return targetSpeed

    def execute(self):
        data = self.sm.lineCam.getLineData()
        isLineVisible = (data is not None) and (data['offset'] is not None)

        # ── LINEA VISIBILE ─────────────────────────────
        if isLineVisible:
            self.shakeActive     = False
            self.blindTurnFrames = 0
            self.lastValidOffset = data['offset']
            
            # Filtro passa-basso sull'offset (ammorbidisce le letture per evitare scatti)
            self.offsetFiltered  = self.offsetFiltered * 0.7 + data['offset'] * 0.3

            # controlla verde → intercetta intersection
            if data.get('greenLeft') or data.get('greenRight') or data.get('uTurn'):
                return "INTERSECTION_HANDLING"

            confirmOffset = data.get('confirmOffset')
            
            # NOVITÀ: Calcola la velocità basata sull'offset FILTRATO, non su quello grezzo
            targetSpeed   = self._computeSpeed(self.offsetFiltered, confirmOffset)
            
            # Appende il dato alla coda. (Uso l'offset grezzo per sterzare rapidamente, 
            # ma la targetSpeed è più fluida perché basata su quello filtrato)
            self.commandQueue.append((data['offset'], targetSpeed))

        # ── LINEA NON VISIBILE ─────────────────────────
        else:
            inTightCurve = abs(self.lastValidOffset) >= self.BLIND_TURN_OFFSET_THRESHOLD

            if inTightCurve and self.blindTurnFrames < self.MAX_BLIND_FRAMES:
                self.blindTurnFrames += 1
                blindOffset = max(-1.0, min(1.0, self.lastValidOffset * self.BLIND_TURN_AMPLIFY))
                self.sm.board.sendControl(blindOffset, self.CURVE_MIN_SPEED, shake=False)
                self.sm.logger.info(
                    f"BLIND TURN [{self.blindTurnFrames}/{self.MAX_BLIND_FRAMES}] off={blindOffset:.2f}"
                )
                return "LINE_FOLLOW"

            self.blindTurnFrames = 0
            return self._gestisciShake()

        # ── PIPELINE COMANDI ──────────────────────────
        if len(self.commandQueue) == self.bufferSize:
            # NOVITÀ: Invece di usare popleft() che svuotava la coda, si prende l'elemento più vecchio
            # (indice 0). Il parametro maxlen=3 della deque espellerà in automatico i vecchi ad ogni append.
            cmd = self.commandQueue[0] 
            self.sm.board.sendControl(cmd[0], cmd[1], shake=False)
        elif len(self.commandQueue) > 0:
            cmd = self.commandQueue[-1]
            self.sm.board.sendControl(cmd[0], cmd[1], shake=False)

        return "LINE_FOLLOW"

    # ── SHAKE INTELLIGENTE ─────────────────────────
    def _gestisciShake(self):
        currentTime = time.time()
        if not self.shakeActive:
            self.shakeActive    = True
            self.shakeStartTime = currentTime
            # Memorizzo da che parte devo iniziare a cercare (basandomi su come ho perso la linea)
            self.initialShakeDir = 1.0 if self.lastValidOffset > 0 else -1.0
            self.sm.logger.warn("INIZIO SHAKE DI RECUPERO...")

        if currentTime - self.shakeStartTime > self.MAX_SHAKE_DURATION:
            self.shakeActive  = False
            self.sm.logger.warn("SHAKE ESAURITO — CONTINUO IN LINE_FOLLOW.")
            return "LINE_FOLLOW"

        elapsed = currentTime - self.shakeStartTime
        
        # NOVITÀ: Movimento basculante matematico perfetto. 
        # Calcolo una "fase" intera. Se pari (0, 2, 4...) va in initialShakeDir.
        # Se dispari (1, 3, 5...) va in direzione opposta. Non si può desincronizzare!
        phase = int(elapsed / self.SHAKE_INTERVAL)
        currentShakeDir = self.initialShakeDir if phase % 2 == 0 else -self.initialShakeDir

        self.sm.board.sendControl(
            currentShakeDir * 1,
            -self.SHAKE_REVERSE_SPEED,
            shake=True
        )
        return "LINE_FOLLOW"