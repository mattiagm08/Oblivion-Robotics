import cv2
import numpy as np
import time
from picamera2 import Picamera2  # type: ignore
from config import (
    LOWER_BLACK, UPPER_BLACK,
    LOWER_GREEN, UPPER_GREEN,
    LOWER_SILVER, UPPER_SILVER,
    LOWER_RED1, UPPER_RED1, LOWER_RED2, UPPER_RED2,
    ROI_LOW_Y, ROI_LOW_H,
    ROI_HIGH_Y, ROI_HIGH_H
)

class LineCamera:
    """
    ###########################################################################
    # LINE CAMERA - FARTHEST-POINT TRACKING                                   #
    ###########################################################################
    # FILOSOFIA:                                                               #
    #   L'offset primario viene calcolato sul punto PIÙ LONTANO della linea   #
    #   visibile nel frame (ROI alta). Se quella ROI non ha linea si scala     #
    #   verso ROI più vicine (mid → low). Così il robot sterza PRIMA della    #
    #   curva invece di reagire quando è già dentro.                          #
    #                                                                          #
    # TRE ROI IN CASCATA (da lontano a vicino):                               #
    #   FAR  (y 15%–30%) → punto di guida principale                          #
    #   MID  (y 35%–52%) → fallback secondario                                #
    #   NEAR (y 57%–75%) → fallback di emergenza + rilevamento marcatori      #
    #                                                                          #
    # CROP ADATTIVO: zoom sulla zona utile (elimina cielo/sfondo lontano).    #
    # EDGE FALLBACK: pixel residui al bordo → offset estremo invece di None.  #
    ###########################################################################
    """

    # Taglia il 30% superiore del frame originale (zona inutile/lontana).
    # Aumenta fino a 0.40 se la camera punta molto in alto.
    CROP_TOP_RATIO = 0.30

    # ------------------------------------------------------------------
    # DEFINIZIONE ROI (rapporti sul frame già croppato)
    # ------------------------------------------------------------------
    # FAR: il punto di guida principale — più lontano possibile
    ROI_FAR_Y  = 0.12
    ROI_FAR_H  = 0.15

    # MID: fallback se FAR non ha linea
    ROI_MID_Y  = 0.32
    ROI_MID_H  = 0.18

    # NEAR: fallback finale + edge pixels per shake detection
    ROI_NEAR_Y = 0.55
    ROI_NEAR_H = 0.22

    def __init__(self, cameraIndex=0, historyLen=3):
        self.Width, self.Height = 320, 240
        self.HistoryLen   = historyLen
        self.GreenHistory = []
        self.lastOffset   = 0.0   # memoria per edge-fallback e blind turn

        self.Picam2 = Picamera2()
        config = self.Picam2.create_video_configuration(
            main={"size": (self.Width, self.Height), "format": "RGB888"}
        )
        self.Picam2.configure(config)
        self.Picam2.start()
        time.sleep(1.0)
        self.Picam2.set_controls({"AeEnable": False, "AwbEnable": False})

        self.LowerBlack  = np.array(LOWER_BLACK)
        self.UpperBlack  = np.array(UPPER_BLACK)
        self.LowerGreen  = np.array(LOWER_GREEN)
        self.UpperGreen  = np.array(UPPER_GREEN)
        self.LowerSilver = np.array(LOWER_SILVER)
        self.UpperSilver = np.array(UPPER_SILVER)
        self.LowerRed1   = np.array(LOWER_RED1)
        self.UpperRed1   = np.array(UPPER_RED1)
        self.LowerRed2   = np.array(LOWER_RED2)
        self.UpperRed2   = np.array(UPPER_RED2)

        self.Kernel = np.ones((3, 3), np.uint8)

    # ------------------------------------------------------------------
    # PREPROCESSING
    # ------------------------------------------------------------------
    def _preprocessFrame(self, frame):
        """Crop zona inutile in alto + resize → zoom sul tratto vicino/medio."""
        cropStartY = int(self.Height * self.CROP_TOP_RATIO)
        cropped    = frame[cropStartY:, :]
        resized    = cv2.resize(cropped, (self.Width, self.Height),
                                interpolation=cv2.INTER_LINEAR)
        return resized

    # ------------------------------------------------------------------
    # MAIN
    # ------------------------------------------------------------------
    def getLineData(self):
        frameRaw = self.Picam2.capture_array()
        if frameRaw is None:
            return None

        frameBGR = cv2.cvtColor(frameRaw, cv2.COLOR_RGB2BGR)
        frame    = self._preprocessFrame(frameBGR)

        blurred = cv2.bilateralFilter(frame, 7, 50, 50)
        hsv     = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        # Maschere
        blackMask  = cv2.inRange(hsv, self.LowerBlack,  self.UpperBlack)
        greenMask  = cv2.inRange(hsv, self.LowerGreen,  self.UpperGreen)
        silverMask = cv2.inRange(hsv, self.LowerSilver, self.UpperSilver)

        blackMask = cv2.morphologyEx(blackMask, cv2.MORPH_CLOSE, self.Kernel)
        greenMask = cv2.morphologyEx(greenMask, cv2.MORPH_OPEN,  self.Kernel)

        # Calcolo ROI in pixel
        farY  = int(self.Height * self.ROI_FAR_Y);  farH  = int(self.Height * self.ROI_FAR_H)
        midY  = int(self.Height * self.ROI_MID_Y);  midH  = int(self.Height * self.ROI_MID_H)
        nearY = int(self.Height * self.ROI_NEAR_Y); nearH = int(self.Height * self.ROI_NEAR_H)

        # ── TRACKING A CASCATA (lontano → vicino) ────────────────────
        # Si usa il punto più lontano disponibile come offset primario.
        # activeRoi indica quale ROI ha fornito l'offset (utile per debug).
        offsetFar,  cxFar  = self._getRobustOffset(blackMask[farY:farY+farH,   :], self.lastOffset)
        offsetMid,  cxMid  = self._getRobustOffset(blackMask[midY:midY+midH,   :], self.lastOffset)
        offsetNear, cxNear = self._getRobustOffset(blackMask[nearY:nearY+nearH, :], self.lastOffset)

        # Offset primario = il più lontano disponibile
        if offsetFar is not None:
            primaryOffset = offsetFar
            primaryCx     = cxFar
            activeRoi     = "FAR"
        elif offsetMid is not None:
            primaryOffset = offsetMid
            primaryCx     = cxMid
            activeRoi     = "MID"
        elif offsetNear is not None:
            primaryOffset = offsetNear
            primaryCx     = cxNear
            activeRoi     = "NEAR"
        else:
            primaryOffset = None
            primaryCx     = None
            activeRoi     = "NONE"

        # Offset di conferma = il più vicino disponibile (per speed clamp)
        confirmOffset = offsetNear if offsetNear is not None else offsetMid

        # Aggiorna memoria solo se abbiamo un rilevamento reale
        if primaryOffset is not None:
            self.lastOffset = primaryOffset

        # ── ARGENTO / ROSSO (su ROI near) ────────────────────────────
        silverDetected = (
            cv2.countNonZero(silverMask[nearY:nearY+nearH, :])
            > (nearH * self.Width * 0.25)
        )
        redMask = cv2.bitwise_or(
            cv2.inRange(hsv, self.LowerRed1, self.UpperRed1),
            cv2.inRange(hsv, self.LowerRed2, self.UpperRed2)
        )
        redDetected = (
            cv2.countNonZero(redMask[nearY:nearY+nearH, :])
            > (nearH * self.Width * 0.15)
        )

        # ── PIXEL AI BORDI per shake (ROI near) ──────────────────────
        edgeW = int(self.Width * 0.15)
        leftBlackPixels  = cv2.countNonZero(blackMask[nearY:nearY+nearH, 0:edgeW])
        rightBlackPixels = cv2.countNonZero(blackMask[nearY:nearY+nearH, self.Width-edgeW:])

        # ── MARCATORI VERDI (ROI mid) ─────────────────────────────────
        contoursG, _ = cv2.findContours(
            greenMask[midY:midY+midH, :],
            cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        lg, rg, fg = False, False, False
        lineRef = primaryCx if primaryCx is not None else self.Width // 2

        for c in contoursG:
            if cv2.contourArea(c) < 400:
                continue
            M = cv2.moments(c)
            if M["m00"] > 0:
                gx = int(M["m10"] / M["m00"])
                gy = int(M["m01"] / M["m00"])
                if gy < midH * 0.4:
                    fg = True
                elif gx < (lineRef - 25):
                    lg = True
                elif gx > (lineRef + 25):
                    rg = True

        self.GreenHistory.append((lg, rg, fg))
        if len(self.GreenHistory) > self.HistoryLen:
            self.GreenHistory.pop(0)

        return {
            # offset = punto PIÙ LONTANO visibile (guida principale)
            "offset":           primaryOffset,
            # confirmOffset = punto vicino (usato per speed clamp)
            "confirmOffset":    confirmOffset,
            # quale ROI ha fornito l'offset (per logging/debug)
            "activeRoi":        activeRoi,
            "leftBlackPixels":  leftBlackPixels,
            "rightBlackPixels": rightBlackPixels,
            "greenLeft":        any(h[0] for h in self.GreenHistory),
            "greenRight":       any(h[1] for h in self.GreenHistory),
            "greenForward":     any(h[2] for h in self.GreenHistory),
            "uTurn":            lg and rg,
            "silver":           silverDetected,
            "red":              redDetected,
            "frame":            frame
        }

    # ------------------------------------------------------------------
    # OFFSET ROBUSTO + EDGE FALLBACK
    # ------------------------------------------------------------------
    def _getRobustOffset(self, maskRoi, fallbackSide=0.0):
        contours, _ = cv2.findContours(
            maskRoi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if contours:
            largest = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest) >= 150:
                M = cv2.moments(largest)
                if M["m00"] > 0:
                    cx        = int(M["m10"] / M["m00"])
                    rawOffset = (cx - (self.Width / 2)) / (self.Width / 2)
                    if abs(rawOffset) < 0.04:
                        rawOffset = 0.0
                    return round(rawOffset, 3), cx

        return self._edgeFallback(maskRoi, fallbackSide)

    def _edgeFallback(self, maskRoi, side):
        """
        Se la linea non è rilevabile nel corpo del frame, cerca pixel
        residui al bordo verso cui stava andando il robot.
        Restituisce ±0.95 invece di None → evita falsi 'linea assente'.
        """
        edgeW     = int(self.Width * 0.12)
        minPixels = 15

        if side > 0.20:
            if cv2.countNonZero(maskRoi[:, self.Width - edgeW:]) >= minPixels:
                return 0.95, self.Width - edgeW // 2
        elif side < -0.20:
            if cv2.countNonZero(maskRoi[:, :edgeW]) >= minPixels:
                return -0.95, edgeW // 2

        return None, None

    def release(self):
        self.Picam2.stop()
        self.Picam2.close()