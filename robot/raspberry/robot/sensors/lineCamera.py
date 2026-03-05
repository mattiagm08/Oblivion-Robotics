import cv2
import numpy as np
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
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
    # LINE CAMERA - SENSOR                                                    #
    ###########################################################################
    # Gestione acquisizione frame da PiCamera2 e rilevamento dei marcatori:  #
    # - offset:       errore laterale della linea nera nella ROI bassa       #
    # - lookAhead:    errore anticipato nella ROI alta (per previsione curva)#
    # - greenLeft:    marcatore verde a sinistra della linea                  #
    # - greenRight:   marcatore verde a destra della linea                   #
    # - greenForward: marcatore verde davanti (incrocio dritto)              #
    # - uTurn:        verde su entrambi i lati → inversione 180°             #
    # - silver:       rilevamento striscia argento (checkpoint / evacuation) #
    # - red:          rilevamento nastro rosso (goal tile)                   #
    ###########################################################################
    # Il filtro temporale sui verdi riduce falsi positivi dovuti a           #
    # oscillazioni rapide o rilevazioni intermittenti dei marcatori.         #
    ###########################################################################
    # MJPEG STREAM: http://<IP_RASPBERRY>:8080                               #
    # Avvia automaticamente un server HTTP sulla porta 8080 che trasmette    #
    # il frame di debug annotato. Apribile da qualsiasi browser in rete.     #
    ###########################################################################
    """

    def __init__(self, cameraIndex=0, historyLen=3, streamPort=8080):
        # IMPOSTAZIONE RISOLUZIONE E STORIA MARCATORI VERDI
        self.Width, self.Height = 320, 240
        self.HistoryLen = historyLen
        self.GreenHistory = []

        # CONFIGURAZIONE E AVVIO PICAMERA2
        self.Picam2 = Picamera2()
        config = self.Picam2.create_video_configuration(
            main={"size": (self.Width, self.Height), "format": "RGB888"}
        )
        self.Picam2.configure(config)
        self.Picam2.start()

        # ATTESA PER STABILIZZAZIONE EXPOSURE E WHITE BALANCE
        time.sleep(1.0)
        self.Picam2.set_controls({"AeEnable": False, "AwbEnable": False})

        # DEFINIZIONE RANGE HSV PER COLORI
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

        # KERNEL PER OPERAZIONI MORFOLOGICHE
        self.Kernel = np.ones((3, 3), np.uint8)

        # FRAME CONDIVISO PER LO STREAM MJPEG
        self._streamFrame = None
        self._streamLock  = threading.Lock()

        # AVVIO SERVER MJPEG IN THREAD SEPARATO
        self._startMjpegServer(streamPort)

    # ######################################################################
    # MJPEG STREAMING
    # ######################################################################

    def _startMjpegServer(self, port):
        camera = self

        class MjpegHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # SILENZIA I LOG HTTP

            def do_GET(self):
                if self.path == "/":
                    self.send_response(200)
                    self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
                    self.end_headers()
                    try:
                        while True:
                            with camera._streamLock:
                                frame = camera._streamFrame
                            if frame is None:
                                time.sleep(0.05)
                                continue
                            ret, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                            if not ret:
                                continue
                            data = jpg.tobytes()
                            self.wfile.write(b"--frame\r\n")
                            self.wfile.write(b"Content-Type: image/jpeg\r\n")
                            self.wfile.write(f"Content-Length: {len(data)}\r\n\r\n".encode())
                            self.wfile.write(data)
                            self.wfile.write(b"\r\n")
                            time.sleep(0.04)  # ~25 FPS
                    except (BrokenPipeError, ConnectionResetError):
                        pass
                else:
                    self.send_response(404)
                    self.end_headers()

        server = HTTPServer(("0.0.0.0", port), MjpegHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

    def _updateStreamFrame(self, frame):
        with self._streamLock:
            self._streamFrame = frame.copy()

    # ######################################################################

    def getLineData(self):

        # ACQUISISCE UN FRAME E RESTITUISCE UN DIZIONARIO CON TUTTI I DATI
        # DI LINEA, MARCATORI VERDI, ARGENTO E ROSSO

        frameRaw = self.Picam2.capture_array()
        if frameRaw is None:
            return None

        frame   = cv2.cvtColor(frameRaw, cv2.COLOR_RGB2BGR)
        blurred = cv2.GaussianBlur(frame, (5, 5), 0)
        hsv     = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        # CREAZIONE MASCHERE COLORE E PULIZIA MORFOLOGICA
        blackMask  = cv2.inRange(hsv, self.LowerBlack,  self.UpperBlack)
        greenMask  = cv2.inRange(hsv, self.LowerGreen,  self.UpperGreen)
        silverMask = cv2.inRange(hsv, self.LowerSilver, self.UpperSilver)
        blackMask  = cv2.morphologyEx(blackMask,  cv2.MORPH_OPEN, self.Kernel)
        greenMask  = cv2.morphologyEx(greenMask,  cv2.MORPH_OPEN, self.Kernel)
        silverMask = cv2.morphologyEx(silverMask, cv2.MORPH_OPEN, self.Kernel)

        # ######################################################################
        # RILEVAMENTO STRISCIA ARGENTO (CHECKPOINT / EVACUATION ZONE)
        # CONTROLLA CHE LA PERCENTUALE DI PIXEL ARGENTO NELLA ROI SUPERI 25%
        # ######################################################################
        silverRoiY, silverRoiH = int(self.Height * ROI_LOW_Y), int(self.Height * ROI_LOW_H)
        silverRoi      = silverMask[silverRoiY:silverRoiY+silverRoiH, :]
        silverPixels   = cv2.countNonZero(silverRoi)
        silverDetected = silverPixels > (silverRoiH * self.Width * 0.25)

        # ######################################################################
        # RILEVAMENTO NASTRO ROSSO (GOAL TILE)
        # DUE RANGE HSV PER COPRIRE ROSSO H=0-10 E H=170-180
        # ######################################################################
        redMask1    = cv2.inRange(hsv, self.LowerRed1, self.UpperRed1)
        redMask2    = cv2.inRange(hsv, self.LowerRed2, self.UpperRed2)
        redMask     = cv2.bitwise_or(redMask1, redMask2)
        redMask     = cv2.morphologyEx(redMask, cv2.MORPH_OPEN, self.Kernel)
        redRoi      = redMask[silverRoiY:silverRoiY+silverRoiH, :]
        redPixels   = cv2.countNonZero(redRoi)
        redDetected = redPixels > (silverRoiH * self.Width * 0.15)

        # ######################################################################
        # RILEVAMENTO LINEA NERA
        # ROI BASSA E ALTA, OFFSET NORMALIZZATO [-1,1]
        # ######################################################################
        roiLowY, roiLowH   = silverRoiY, silverRoiH
        roiHighY, roiHighH = int(self.Height * ROI_HIGH_Y), int(self.Height * ROI_HIGH_H)
        offsetLow, cxLow   = self._getRobustOffset(blackMask[roiLowY:roiLowY+roiLowH, :])
        offsetHigh, _      = self._getRobustOffset(blackMask[roiHighY:roiHighY+roiHighH, :])

        # ######################################################################
        # RILEVAMENTO MARCATORI VERDI
        # ROI INFERIORE (AVVICINAMENTO INCROCIO)
        # ######################################################################
        greenRoiY, greenRoiH = int(self.Height * 0.50), int(self.Height * 0.30)
        greenRoi     = greenMask[greenRoiY:greenRoiY+greenRoiH, :]
        contoursG, _ = cv2.findContours(greenRoi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        leftGreen    = False
        rightGreen   = False
        greenForward = False
        greenCenters = []

        # CENTRO LINEA DI RIFERIMENTO (FALLBACK AL CENTRO FRAME)
        lineRef            = cxLow if cxLow is not None else self.Width // 2
        immediateThreshold = greenRoiH * 0.65  # META' SUPERIORE ROI = "AVANTI"

        # ANALISI CONTORNI VERDI
        for c in contoursG:
            area = cv2.contourArea(c)
            if area < 600:  # SCARTA RUMORE
                continue
            bx, by, bw, bh = cv2.boundingRect(c)
            if bh == 0 or not (0.3 < bw/bh < 3.0):  # FILTRO PROPORZIONI QUADRATO
                continue
            M = cv2.moments(c)
            if M["m00"] > 0:
                gx = int(M["m10"]/M["m00"])
                gy = int(M["m01"]/M["m00"])
                greenCenters.append((gx, gy))
                if gy < immediateThreshold:
                    greenForward = True  # MARCATORE AVANTI
                else:
                    if gx < (lineRef - 25):
                        leftGreen = True
                    elif gx > (lineRef + 25):
                        rightGreen = True

        # ######################################################################
        # FILTRO TEMPORALE SUI MARCATORI VERDI
        # EVITA OSCILLAZIONI IN RILEVAMENTO RAPIDO
        # ######################################################################
        self.GreenHistory.append((leftGreen, rightGreen, greenForward))
        if len(self.GreenHistory) > self.HistoryLen:
            self.GreenHistory.pop(0)

        # STABILIZZAZIONE TRAMITE MAGGIORANZA DEI VALORI STORICI
        leftGreen    = max(set([h[0] for h in self.GreenHistory]), key=[h[0] for h in self.GreenHistory].count)
        rightGreen   = max(set([h[1] for h in self.GreenHistory]), key=[h[1] for h in self.GreenHistory].count)
        greenForward = max(set([h[2] for h in self.GreenHistory]), key=[h[2] for h in self.GreenHistory].count)

        uTurn = leftGreen and rightGreen  # DEAD-END → INVERSIONE 180°

        data = {
            "offset":       offsetLow,
            "lookAhead":    offsetHigh,
            "greenLeft":    leftGreen,
            "greenRight":   rightGreen,
            "greenForward": greenForward,
            "uTurn":        uTurn,
            "silver":       silverDetected,
            "red":          redDetected,
            "lineX":        lineRef,
            "greenCenters": greenCenters,
            "frame":        frame,
            "roiViz":       [(roiLowY, roiLowH), (roiHighY, roiHighH), (greenRoiY, greenRoiH)]
        }

        # AGGIORNA IL FRAME DELLO STREAM CON L'ANNOTAZIONE DEBUG
        self._updateStreamFrame(self._buildDebugFrame(data))

        return data

    def _getRobustOffset(self, maskRoi):

        # CALCOLA IL CONTORNO NERO PIU' GRANDE NELLA ROI E RITORNA:
        # - OFFSET NORMALIZZATO [-1,1]
        # - POSIZIONE PIXEL CX
        # RESTITUISCE (None, None) SE LINEA NON TROVATA O TROPPO PICCOLA.

        contours, _ = cv2.findContours(maskRoi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None, None
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) < 150:
            return None, None
        M = cv2.moments(largest)
        if M["m00"] > 0:
            cx     = int(M["m10"]/M["m00"])
            offset = (cx - (self.Width / 2)) / (self.Width / 2)
            return round(offset, 3), cx
        return None, None

    def _buildDebugFrame(self, data):

        # COSTRUISCE IL FRAME ANNOTATO DA INVIARE ALLO STREAM MJPEG.

        frame  = data["frame"].copy()
        colors = [(0, 0, 255), (255, 0, 0), (0, 255, 0)]  # ROSSO, BLU, VERDE
        for i, (y, h) in enumerate(data["roiViz"]):
            cv2.rectangle(frame, (0, y), (self.Width, y + h), colors[i], 1)

        greenRoiY = data["roiViz"][2][0]
        for (gx, gy) in data["greenCenters"]:
            cv2.circle(frame, (gx, greenRoiY + gy), 7, (0, 255, 0), -1)

        status = (
            f"L:{int(data['greenLeft'])} R:{int(data['greenRight'])} "
            f"F:{int(data['greenForward'])} U:{int(data['uTurn'])} "
            f"Off:{data['offset']}"
        )
        cv2.putText(frame, status, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        return frame

    def release(self):

        # FERMA LA TELECAMERA E RILASCIA LE RISORSE ASSOCIATE.

        self.Picam2.stop()