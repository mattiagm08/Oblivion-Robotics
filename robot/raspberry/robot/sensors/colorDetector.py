import cv2
import numpy as np
from config import LOWER_SILVER, UPPER_SILVER

class ColorDetector:
    """
    ###########################################################################
    # COLOR DETECTOR - SENSOR                                                 #
    ###########################################################################
    # Analizza porzioni specifiche del frame per identificare materiali       #
    # speciali come il nastro d'argento.                                      #
    ###########################################################################
    """
    def __init__(self):
        # CARICAMENTO SOGLIE HSV PER RILEVAMENTO ARGENTO DA CONFIG
        self.lowerSilver = np.array(LOWER_SILVER)
        self.upperSilver = np.array(UPPER_SILVER)
        
        # KERNEL 5x5 PER PULIZIA MORFOLOGICA DELLA MASCHERA (RIMOZIONE RUMORE)
        self.kernel = np.ones((5, 5), np.uint8)

    def checkForSilver(self, frame):
        """
        ANALIZZA LA PARTE CENTRALE DEL FRAME PER RILEVARE L'ARGENTO.
        RITORNA TRUE SE LA PERCENTUALE DI PIXEL ARGENTO SUPERA LA SOGLIA.
        """

        # DIMENSIONI FRAME (ALTEZZA, LARGHEZZA, CANALI)
        h, w, _ = frame.shape
        
        # #####################################################################
        # FASE 1: DEFINIZIONE ROI CENTRALE                                    #
        # SELEZIONA LA FASCIA ORIZZONTALE CENTRALE DEL FRAME                  #
        # #####################################################################
        roi_y = int(h * 0.50)
        roi_h = int(h * 0.20)
        roi = frame[roi_y : roi_y + roi_h, :]

        # #####################################################################
        # FASE 2: CONVERSIONE IN HSV E CREAZIONE MASCHERA                     #
        # CONVERSIONE PER STABILITÀ ALLA LUCE E ISOLAMENTO DEL COLORE ARGENTO #
        # #####################################################################
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lowerSilver, self.upperSilver)

        # #####################################################################
        # FASE 3: PULIZIA MORFOLOGICA                                         #
        # RIMOZIONE PIXEL SPURI E RUMORE PER AFFIDABILITÀ DEL RILEVAMENTO     #
        # #####################################################################
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)

        # #####################################################################
        # FASE 4: CALCOLO PERCENTUALE PIXEL ARGENTO                           #
        # CONTEGGIO PIXEL BIANCHI NELLA MASCHERA E CALCOLO PERCENTUALE ROI    #
        # #####################################################################
        silver_pixel_count = np.sum(mask == 255)
        total_pixels = roi.shape[0] * roi.shape[1]
        percentage = (silver_pixel_count / total_pixels) * 100

        # #####################################################################
        # FASE 5: VERIFICA SOGLIA                                             #
        # RITORNA TRUE SE LA PERCENTUALE PIXEL ARGENTO SUPERIORE AL 15%       #
        # #####################################################################
        return percentage > 15.0