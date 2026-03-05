"""
###########################################################################
# DEBUG TOOL: SISTEMA VISIONE RCJ RESCUE LINE 2026 - RASPBERRY            #
###########################################################################
# Verifica ROI, offset, look-ahead, marcatori verdi, argento e rosso.     #
# Usa lineCamera.py (PiCamera2).                                          #
# Premi 'q' per uscire.                                                   #
###########################################################################
"""

import cv2
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sensors.lineCamera import LineCamera
from config import MAX_SPEED, MIN_SPEED


def main():
    print("[INFO] DEBUG VISIONE RCJ AVVIATO - RASPBERRY MODE")

    cam = LineCamera()
    print("Premi 'q' per uscire.")

    while True:
        data = cam.getLineData()
        if data is None:
            continue

        frame = data['frame']

        # ##################################################################
        # ROI STEER (bassa, rossa)
        # ##################################################################
        # FIX: era 'roi_viz' → chiave corretta è 'roiViz'
        rL_y, rL_h = data['roiViz'][0]
        cv2.rectangle(frame, (0, rL_y), (320, rL_y + rL_h), (0, 0, 255), 2)
        cv2.putText(frame, "STEER", (5, rL_y + 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        # ##################################################################
        # ROI SPEED / LOOK-AHEAD (alta, blu)
        # ##################################################################
        rH_y, rH_h = data['roiViz'][1]
        cv2.rectangle(frame, (0, rH_y), (320, rH_y + rH_h), (255, 0, 0), 2)
        cv2.putText(frame, "SPEED", (5, rH_y + 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

        # ##################################################################
        # ROI VERDE (giallo-ciano)
        # ##################################################################
        rG_y, rG_h = data['roiViz'][2]
        cv2.rectangle(frame, (0, rG_y), (320, rG_y + rG_h), (0, 255, 255), 1)

        # ##################################################################
        # OFFSET E LOOK-AHEAD (cerchi)
        # ##################################################################
        if data['offset'] is not None:
            cx_low = int((data['offset'] * 160) + 160)
            cv2.circle(frame, (cx_low, rL_y + (rL_h // 2)), 10, (0, 255, 0), -1)
            cv2.putText(frame, f"Off: {data['offset']:.2f}",
                        (cx_low - 20, rL_y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

        # FIX: era 'look_ahead' → chiave corretta è 'lookAhead'
        if data['lookAhead'] is not None:
            cx_high = int((data['lookAhead'] * 160) + 160)
            cv2.circle(frame, (cx_high, rH_y + (rH_h // 2)), 7, (255, 255, 0), -1)

        # ##################################################################
        # SIMULAZIONE VELOCITÀ
        # ##################################################################
        offVal  = data['offset']    if data['offset']    is not None else 0.0
        # FIX: era 'look_ahead' → chiave corretta è 'lookAhead'
        lookVal = data['lookAhead'] if data['lookAhead'] is not None else offVal

        curveFactor = (abs(offVal) * 0.4) + (abs(lookVal) * 0.6)
        simSpeed    = int(MAX_SPEED - (curveFactor * (MAX_SPEED - MIN_SPEED)))
        simSpeed    = max(MIN_SPEED, simSpeed)

        print(f"[DEBUG] Off:{offVal:+.2f}  Look:{lookVal:+.2f}  "
              f"Spd:{simSpeed}  "
              f"L:{int(data['greenLeft'])} R:{int(data['greenRight'])} "
              f"U:{int(data['uTurn'])} S:{int(data['silver'])} "
              f"Red:{int(data['red'])}")

        # ##################################################################
        # MARCATORI VERDI
        # ##################################################################
        # FIX: era 'green_left'/'green_right' → chiavi corrette sono 'greenLeft'/'greenRight'
        if data['greenLeft']:
            cv2.rectangle(frame, (0, rG_y), (160, rG_y + rG_h),
                          (0, 200, 0), -1)
            cv2.putText(frame, "GREEN L", (10, rG_y + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        if data['greenRight']:
            cv2.rectangle(frame, (160, rG_y), (320, rG_y + rG_h),
                          (0, 200, 0), -1)
            cv2.putText(frame, "GREEN R", (170, rG_y + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        if data['uTurn']:
            cv2.putText(frame, "U-TURN", (100, rG_y + rG_h - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # ##################################################################
        # ARGENTO E ROSSO
        # ##################################################################
        if data['silver']:
            cv2.rectangle(frame, (0, 0), (320, 30), (180, 180, 180), -1)
            cv2.putText(frame, "SILVER - EVACUATION ZONE", (10, 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)

        if data['red']:
            cv2.rectangle(frame, (0, 0), (320, 30), (0, 0, 200), -1)
            cv2.putText(frame, "RED - GOAL TILE", (10, 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

        # ##################################################################
        # MOSTRA FRAME
        # ##################################################################
        cv2.imshow("DEBUG RCJ 2026 - RASPBERRY", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()
    print("[INFO] Debug terminato.")


if __name__ == "__main__":
    main()