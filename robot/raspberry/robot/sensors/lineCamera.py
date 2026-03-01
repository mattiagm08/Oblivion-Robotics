import cv2
import numpy as np
from config import (
    LOWER_BLACK, UPPER_BLACK, 
    LOWER_GREEN, UPPER_GREEN,
    ROI_LOW_Y, ROI_LOW_H,
    ROI_HIGH_Y, ROI_HIGH_H
)

class LineCamera:
    """
    ###########################################################################
    # LINE CAMERA - SENSOR                                                    #
    ###########################################################################
    # Gestisce il rilevamento della linea su due livelli (vicino e lontano)   #
    # e identifica i marcatori verdi per gli incroci.                         #
    # Supporta il flag per la ridondanza del rilevamento argento.             #
    ###########################################################################
    """
    def __init__(self, cameraIndex=0):
        # INIZIALIZZAZIONE CAMERA E DIMENSIONI FRAME
        self.cap = cv2.VideoCapture(cameraIndex)
        self.width, self.height = 320, 240
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        # CARICAMENTO RANGE HSV PER NERO E VERDE DA CONFIG
        self.lowerBlack = np.array(LOWER_BLACK)
        self.upperBlack = np.array(UPPER_BLACK)
        self.lowerGreen = np.array(LOWER_GREEN)
        self.upperGreen = np.array(UPPER_GREEN)
        
        # KERNEL 5x5 PER PULIZIA MORFOLOGICA (RIMOZIONE RUMORE)
        self.kernel = np.ones((5, 5), np.uint8)

    def getLineData(self):
        
        # CATTURA UN FRAME E PROCESSA LE ROI PER ESTRARE OFFSET E MARCATORI.
        # RITORNA UN DIZIONARIO CON I DATI ELABORATI PER LA FSM.
        
        ret, frame = self.cap.read()
        if not ret: 
            return None
            
        # #####################################################################
        # FASE 1: CONVERSIONE IN HSV                                          #
        # #####################################################################
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # #####################################################################
        # FASE 2: CREAZIONE MASCHERE BINARIE                                  #
        # #####################################################################
        blackMask = cv2.inRange(hsv, self.lowerBlack, self.upperBlack)
        greenMask = cv2.inRange(hsv, self.lowerGreen, self.upperGreen)
        
        # #####################################################################
        # FASE 3: PULIZIA MORFOLOGICA MASCHERE                                #
        # #####################################################################
        blackMask = cv2.morphologyEx(blackMask, cv2.MORPH_OPEN, self.kernel)
        greenMask = cv2.morphologyEx(greenMask, cv2.MORPH_OPEN, self.kernel)

        # #####################################################################
        # FASE 4: ROI BASSA - GUIDA DI PRECISIONE                             #
        # #####################################################################
        roiLowY = int(self.height * ROI_LOW_Y)
        roiLowH = int(self.height * ROI_LOW_H)
        roiLow = blackMask[roiLowY : roiLowY + roiLowH, :]
        offsetLow = self._calculate_offset(roiLow)

        # #####################################################################
        # FASE 5: ROI ALTA - LOOK-AHEAD                                       #
        # #####################################################################
        roiHighY = int(self.height * ROI_HIGH_Y)
        roiHighH = int(self.height * ROI_HIGH_H)
        roiHigh = blackMask[roiHighY : roiHighY + roiHighH, :]
        offsetHigh = self._calculate_offset(roiHigh)

        # #####################################################################
        # FASE 6: RILEVAMENTO MARCATORI VERDI                                 #
        # #####################################################################
        greenRoiY = int(self.height * 0.60)
        greenRoiH = int(self.height * 0.20)
        greenRoi = greenMask[greenRoiY : greenRoiY + greenRoiH, :]

        # CONTEGGIO PIXEL VERDI SUDDIVISI A SINISTRA E DESTRA
        leftGreenCount = np.sum(greenRoi[:, :self.width//2] == 255)
        rightGreenCount = np.sum(greenRoi[:, self.width//2:] == 255)

        # VERIFICA SOGLIA MINIMA PIXEL (CALIBRATA PER 320x240)
        leftGreen = leftGreenCount > 500
        rightGreen = rightGreenCount > 500

        # #####################################################################
        # FASE 7: RITORNO DATI                                                #
        # #####################################################################
        return {
            "offset": offsetLow,       
            "look_ahead": offsetHigh,  
            "green_left": leftGreen,
            "green_right": rightGreen,
            "frame": frame,            
            "roi_viz": [(roiLowY, roiLowH), (roiHighY, roiHighH), (greenRoiY, greenRoiH)]
        }

    def _calculate_offset(self, roi):
        
        #CALCOLO OFFSET NORMALIZZATO (-1.0 A 1.0) BASATO SUI MOMENTI D'IMMAGINE.
        # 0.0 = CENTRO, -1.0 = TUTTO A SINISTRA, 1.0 = TUTTO A DESTRA.
        
        M = cv2.moments(roi)
        # SOGLIA MINIMA DI 400 PIXEL PER EVITARE RILEVAMENTI SPURI
        if M["m00"] > 400:  
            cx = int(M["m10"] / M["m00"])
            # CALCOLO OFFSET NORMALIZZATO RISPETTO AL CENTRO DELLA ROI
            offset = (cx - (self.width / 2)) / (self.width / 2)
            return round(offset, 3)
        return None

    def release(self):
        # RILASCIO RISORSE CAMERA
        if self.cap.isOpened():
            self.cap.release()