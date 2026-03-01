"""
###########################################################################
# DEBUG TOOL: SISTEMA VISIONE RCJ RESCUE LINE 2026                        #
###########################################################################
# STRUMENTO DI ANALISI VISIVA PER VERIFICA ROI, OFFSET, LOOK-AHEAD        #
# E SIMULAZIONE DINAMICA DELLA VELOCITÀ CALCOLATA DAL CONTROLLO.          #
###########################################################################
"""

import cv2
import sys
import os
import numpy as np

# AGGIUNTA DEL PERCORSO ROOT DEL PROGETTO PER IMPORT CORRETTI
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sensors.lineCamera import LineCamera
from config import MAX_SPEED, MIN_SPEED


def main():
    # INIZIALIZZAZIONE CAMERA (INDEX 0 = WEBCAM PRINCIPALE O PICAMERA)
    cam = LineCamera(cameraIndex=0)

    print("##########################################")
    print("# DEBUG VISIONE RCJ RESCUE LINE 2026     #")
    print("##########################################")
    print("# ROSSO: ROI BASSA (CONTROLLO STERZO)    #")
    print("# BLU:   ROI ALTA (LOOK-AHEAD/VELOCITÀ)  #")
    print("# GIALLO:ROI VERDE (RILEVAMENTO MARKER)  #")
    print("##########################################")
    print("Premi 'q' per uscire.")

    # LOOP PRINCIPALE DI ACQUISIZIONE FRAME
    while True:

        # ACQUISIZIONE DATI ELABORATI DAL MODULO VISIONE
        data = cam.getLineData()
        if data is None:
            continue

        frame = data['frame']

        # ##################################################################
        # DISEGNO DELLE ROI (REGION OF INTEREST)                           #
        # ##################################################################

        # ROI BASSA - CONTROLLO STERZO IMMEDIATO
        rL_y, rL_h = data['roi_viz'][0]
        cv2.rectangle(frame, (0, rL_y), (320, rL_y + rL_h), (0, 0, 255), 2)
        cv2.putText(frame, "STEER", (5, rL_y + 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        # ROI ALTA - LOOK-AHEAD PER REGOLAZIONE VELOCITÀ
        rH_y, rH_h = data['roi_viz'][1]
        cv2.rectangle(frame, (0, rH_y), (320, rH_y + rH_h), (255, 0, 0), 2)
        cv2.putText(frame, "SPEED", (5, rH_y + 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

        # ROI VERDE - RILEVAMENTO MARCATORI INCROCIO
        rG_y, rG_h = data['roi_viz'][2]
        cv2.rectangle(frame, (0, rG_y), (320, rG_y + rG_h), (0, 255, 255), 1)

        # ##################################################################
        # VISUALIZZAZIONE OFFSET E LOOK-AHEAD                              #
        # ##################################################################

        # PUNTO VERDE = OFFSET ATTUALE (CENTRO LINEA NELLA ROI BASSA)
        if data['offset'] is not None:
            cx_low = int((data['offset'] * 160) + 160)
            cv2.circle(frame, (cx_low, rL_y + (rL_h // 2)), 10, (0, 255, 0), -1)
            cv2.putText(frame, f"Off: {data['offset']}",
                        (cx_low - 20, rL_y - 5), 0, 0.4, (0, 255, 0), 1)

        # PUNTO AZZURRO = LOOK-AHEAD (STIMA TRAIETTORIA FUTURA)
        if data['look_ahead'] is not None:
            cx_high = int((data['look_ahead'] * 160) + 160)
            cv2.circle(frame, (cx_high, rH_y + (rH_h // 2)),
                       7, (255, 255, 0), -1)

        # ##################################################################
        # SIMULAZIONE LOGICA VELOCITÀ (COME IN LINEFOLLOW)                 #
        # ##################################################################

        look_val = data['look_ahead'] if data['look_ahead'] is not None else (data['offset'] if data['offset'] is not None else 0.0)
        off_val = data['offset'] if data['offset'] is not None else 0.0

        curve_factor = (abs(off_val) * 0.4) + (abs(look_val) * 0.6)

        sim_speed = int(MAX_SPEED - (curve_factor * (MAX_SPEED - MIN_SPEED)))
        sim_speed = max(MIN_SPEED, sim_speed)

        # ##################################################################
        # OVERLAY INFORMAZIONI SU FRAME                                    #
        # ##################################################################

        cv2.putText(frame, f"SPEED: {sim_speed}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (255, 255, 255), 2)

        if data['green_left']:
            cv2.rectangle(frame, (0, rG_y), (160, rG_y + rG_h),
                          (0, 255, 0), -1)
            cv2.putText(frame, "GREEN L",
                        (10, rG_y + 20), 0, 0.6, (0, 0, 0), 2)

        if data['green_right']:
            cv2.rectangle(frame, (160, rG_y), (320, rG_y + rG_h),
                          (0, 255, 0), -1)
            cv2.putText(frame, "GREEN R",
                        (170, rG_y + 20), 0, 0.6, (0, 0, 0), 2)

        # ##################################################################
        # VISUALIZZAZIONE FRAME DI DEBUG                                   #
        # ##################################################################

        cv2.imshow("DEBUG RCJ 2026 - LOOK AHEAD SYSTEM", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()