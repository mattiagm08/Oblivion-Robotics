import cv2
import numpy as np
import time
try:
    from picamera2 import Picamera2  # type: ignore
    HAS_PICAMERA = True
except ImportError:
    HAS_PICAMERA = False

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
    # LINE CAMERA - SENSOR                                                    #
    ###########################################################################
    # Gestione acquisizione frame e rilevamento marcatori verdi, argento e rosso
    ###########################################################################
    """

    def __init__(self, cameraIndex=0, historyLen=3, usePiCamera=True):
        # IMPOSTAZIONE RISOLUZIONE E STORIA MARCATORI VERDI
        self.Width, self.Height = 320, 240
        self.HistoryLen = historyLen
        self.GreenHistory = []

        # SE SI USA PICAMERA2
        self.usePiCamera = usePiCamera and HAS_PICAMERA
        if self.usePiCamera:
            self.Picam2 = Picamera2()
            config = self.Picam2.create_video_configuration(
                main={"size": (self.Width, self.Height), "format": "RGB888"}
            )
            self.Picam2.configure(config)
            self.Picam2.start()
            time.sleep(1.0)  # stabilizzazione sensore
            self.Picam2.set_controls({"AeEnable": False, "AwbEnable": False})
        else:
            # ALTRIMENTI USO OPENCV VIDEO CAPTURE PER WEBCAM
            self.cap = cv2.VideoCapture(cameraIndex)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.Width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.Height)
            time.sleep(1.0)

        # RANGE HSV COLORI
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

        self.Kernel = np.ones((3,3), np.uint8)

    # ######################################################################

    def getLineData(self):
        # ACQUISISCE FRAME DAL SENSORE SELEZIONATO
        if self.usePiCamera:
            frameRaw = self.Picam2.capture_array()
            if frameRaw is None:
                return None
            frame = cv2.cvtColor(frameRaw, cv2.COLOR_RGB2BGR)
        else:
            ret, frame = self.cap.read()
            if not ret:
                return None

        blurred = cv2.GaussianBlur(frame, (5,5), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        # CREAZIONE MASCHERE
        blackMask = cv2.inRange(hsv, self.LowerBlack, self.UpperBlack)
        greenMask = cv2.inRange(hsv, self.LowerGreen, self.UpperGreen)
        silverMask = cv2.inRange(hsv, self.LowerSilver, self.UpperSilver)
        blackMask = cv2.morphologyEx(blackMask, cv2.MORPH_OPEN, self.Kernel)
        greenMask = cv2.morphologyEx(greenMask, cv2.MORPH_OPEN, self.Kernel)
        silverMask = cv2.morphologyEx(silverMask, cv2.MORPH_OPEN, self.Kernel)

        # RILEVAMENTO ARGENTO
        silverRoiY, silverRoiH = int(self.Height * ROI_LOW_Y), int(self.Height * ROI_LOW_H)
        silverRoi = silverMask[silverRoiY:silverRoiY+silverRoiH, :]
        silverPixels = cv2.countNonZero(silverRoi)
        silverDetected = silverPixels > (silverRoiH * self.Width * 0.25)

        # RILEVAMENTO ROSSO
        redMask1 = cv2.inRange(hsv, self.LowerRed1, self.UpperRed1)
        redMask2 = cv2.inRange(hsv, self.LowerRed2, self.UpperRed2)
        redMask = cv2.bitwise_or(redMask1, redMask2)
        redMask = cv2.morphologyEx(redMask, cv2.MORPH_OPEN, self.Kernel)
        redRoi = redMask[silverRoiY:silverRoiY+silverRoiH, :]
        redPixels = cv2.countNonZero(redRoi)
        redDetected = redPixels > (silverRoiH * self.Width * 0.15)

        # RILEVAMENTO LINEA NERA
        roiLowY, roiLowH = silverRoiY, silverRoiH
        roiHighY, roiHighH = int(self.Height*ROI_HIGH_Y), int(self.Height*ROI_HIGH_H)
        offsetLow, cxLow = self._getRobustOffset(blackMask[roiLowY:roiLowY+roiLowH, :])
        offsetHigh, _ = self._getRobustOffset(blackMask[roiHighY:roiHighY+roiHighH, :])

        # RILEVAMENTO MARCATORI VERDI
        greenRoiY, greenRoiH = int(self.Height*0.5), int(self.Height*0.3)
        greenRoi = greenMask[greenRoiY:greenRoiY+greenRoiH, :]
        contoursG, _ = cv2.findContours(greenRoi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        leftGreen, rightGreen, greenForward = False, False, False
        greenCenters = []
        lineRef = cxLow if cxLow is not None else self.Width//2
        immediateThreshold = greenRoiH * 0.65

        for c in contoursG:
            area = cv2.contourArea(c)
            if area < 600:
                continue
            bx, by, bw, bh = cv2.boundingRect(c)
            if bh == 0 or not (0.3 < bw/bh < 3.0):
                continue
            M = cv2.moments(c)
            if M["m00"] > 0:
                gx = int(M["m10"]/M["m00"])
                gy = int(M["m01"]/M["m00"])
                greenCenters.append((gx, gy))
                if gy < immediateThreshold:
                    greenForward = True
                else:
                    if gx < (lineRef-25):
                        leftGreen = True
                    elif gx > (lineRef+25):
                        rightGreen = True

        # FILTRO TEMPORALE VERDI
        self.GreenHistory.append((leftGreen, rightGreen, greenForward))
        if len(self.GreenHistory) > self.HistoryLen:
            self.GreenHistory.pop(0)
        leftGreen = max(set([h[0] for h in self.GreenHistory]), key=[h[0] for h in self.GreenHistory].count)
        rightGreen = max(set([h[1] for h in self.GreenHistory]), key=[h[1] for h in self.GreenHistory].count)
        greenForward = max(set([h[2] for h in self.GreenHistory]), key=[h[2] for h in self.GreenHistory].count)
        uTurn = leftGreen and rightGreen

        return {
            "offset": offsetLow,
            "lookAhead": offsetHigh,
            "greenLeft": leftGreen,
            "greenRight": rightGreen,
            "greenForward": greenForward,
            "uTurn": uTurn,
            "silver": silverDetected,
            "red": redDetected,
            "lineX": lineRef,
            "greenCenters": greenCenters,
            "frame": frame,
            "roiViz": [(roiLowY, roiLowH), (roiHighY, roiHighH), (greenRoiY, greenRoiH)]
        }

    def _getRobustOffset(self, maskRoi):
        contours, _ = cv2.findContours(maskRoi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None, None
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) < 150:
            return None, None
        M = cv2.moments(largest)
        if M["m00"] > 0:
            cx = int(M["m10"]/M["m00"])
            offset = (cx - self.Width/2) / (self.Width/2)
            return round(offset, 3), cx
        return None, None

    def showDebug(self, data):
        if data is None:
            return
        frame = data["frame"].copy()
        colors = [(0,0,255),(255,0,0),(0,255,0)]
        for i, (y,h) in enumerate(data["roiViz"]):
            cv2.rectangle(frame, (0,y), (self.Width,y+h), colors[i], 1)
        greenRoiY = data["roiViz"][2][0]
        for (gx, gy) in data["greenCenters"]:
            cv2.circle(frame, (gx, greenRoiY+gy), 7, (0,255,0), -1)
        status = f"L:{int(data['greenLeft'])} R:{int(data['greenRight'])} F:{int(data['greenForward'])} U:{int(data['uTurn'])} Off:{data['offset']}"
        cv2.putText(frame, status, (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0,255,255),1)
        cv2.imshow("Debug", frame)
        cv2.waitKey(1)

    def release(self):
        if self.usePiCamera:
            self.Picam2.stop()
        else:
            self.cap.release()