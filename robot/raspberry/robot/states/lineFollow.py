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

    def __init__(self, stateMachine):
        super().__init__(stateMachine)

        self.shakeActive      = False
        self.shakeStartTime   = 0
        self.shakeDirection   = 1.0
        self.shakeAttempt     = 0
        self.lastValidOffset  = 0.0
        self.maxShakeDuration = 2.0

        self.bufferSize   = 3
        self.commandQueue = deque(maxlen=self.bufferSize)
        self.blindTurnFrames = 0

        if self.CURVE_MIN_SPEED is None:
            self.CURVE_MIN_SPEED = MIN_SPEED + 10

        if self.SHAKE_REVERSE_SPEED is None:
            self.SHAKE_REVERSE_SPEED = MIN_SPEED

    def _computeSpeed(self, offsetFar, offsetNear):
        speedRange  = MAX_SPEED - MIN_SPEED
        targetSpeed = int(MAX_SPEED - speedRange * (abs(offsetFar) ** self.CURVE_SPEED_EXPONENT))
        targetSpeed = max(MIN_SPEED, targetSpeed)

        if abs(offsetFar) >= self.CURVE_SLOW_THRESHOLD:
            targetSpeed = min(targetSpeed, self.CURVE_MIN_SPEED)

        if offsetNear is not None and abs(offsetNear) >= self.CURVE_CONFIRM_THRESHOLD:
            targetSpeed = min(targetSpeed, self.CURVE_MIN_SPEED)

        return targetSpeed

    def execute(self):
        data = self.sm.lineCam.getLineData()
        isLineVisible = (data is not None) and (data['offset'] is not None)

        if isLineVisible:
            self.shakeActive     = False
            self.shakeAttempt    = 0
            self.blindTurnFrames = 0
            self.lastValidOffset = data['offset']

            confirmOffset = data.get('confirmOffset')
            targetSpeed   = self._computeSpeed(data['offset'], confirmOffset)
            self.commandQueue.append((data['offset'], targetSpeed))

        else:
            inTightCurve = abs(self.lastValidOffset) >= self.BLIND_TURN_OFFSET_THRESHOLD

            if inTightCurve and self.blindTurnFrames < self.MAX_BLIND_FRAMES:
                self.blindTurnFrames += 1
                blindOffset = max(-1.0, min(1.0,
                                  self.lastValidOffset * self.BLIND_TURN_AMPLIFY))
                self.sm.board.sendControl(blindOffset, self.CURVE_MIN_SPEED, shake=False)
                self.sm.logger.info(
                    f"BLIND TURN [{self.blindTurnFrames}/{self.MAX_BLIND_FRAMES}] "
                    f"off={blindOffset:.2f}"
                )
                return "LINE_FOLLOW"

            self.blindTurnFrames = 0

            # GAP DISABILITATO — shake sempre, non si esce mai da LINE_FOLLOW
            return self._gestisciShake(None)

        # ── PIPELINE ─────────────────────────────────────────────────
        if len(self.commandQueue) >= self.bufferSize:
            cmd = self.commandQueue.popleft()
            self.sm.board.sendControl(cmd[0], cmd[1], shake=False)
        elif len(self.commandQueue) > 0:
            cmd = self.commandQueue[-1]
            self.sm.board.sendControl(cmd[0], cmd[1], shake=False)

        return "LINE_FOLLOW"

    def _gestisciShake(self, data):
        currentTime = time.time()
        if not self.shakeActive:
            self.shakeActive    = True
            self.shakeStartTime = currentTime
            self.shakeAttempt   = 1
            self.shakeDirection = 1.0 if self.lastValidOffset > 0 else -1.0
            self.sm.logger.warn("INIZIO SHAKE DI RECUPERO...")

        if currentTime - self.shakeStartTime > self.maxShakeDuration:
            self.shakeActive  = False
            self.shakeAttempt = 0
            self.sm.logger.warn("SHAKE ESAURITO — CONTINUO IN LINE_FOLLOW.")
            return "LINE_FOLLOW"

        elapsed = currentTime - self.shakeStartTime
        if elapsed > (self.shakeAttempt * 0.20):
            self.shakeDirection *= -1.0
            self.shakeAttempt   += 1

        self.sm.board.sendControl(
            self.shakeDirection * 0.9,
            -self.SHAKE_REVERSE_SPEED,
            shake=True
        )
        return "LINE_FOLLOW"