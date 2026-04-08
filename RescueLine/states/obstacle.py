
import cv2 # type: ignore
import numpy as np # type: ignore
import comm
import time

# COSTANTI DI TEMPO PER LA MANOVRA

TIME_TURN = 0.5    
TIME_STRAIGHT = 1.0 

# FUNZIONE PRINCIPALE DI EVITAMENTO OSTACOLO

def run(cleanImage):

    # LOGICA DI EVITAMENTO (SEQUENZA DI ESEMPIO)

    print("ESECUZIONE MANOVRA OSTACOLO...")

    # 1. CURVA A DESTRA PER USCIRE DALLA LINEA

    comm.right()
    time.sleep(TIME_TURN)

    # 2. AVANTI PER SUPERARE L'OSTACOLO

    comm.forward()
    time.sleep(TIME_STRAIGHT)

    # 3. CURVA A SINISTRA PER TORNARE VERSO LA LINEA

    comm.left()
    time.sleep(TIME_TURN)

    # 4. AVANTI FINCHÉ NON RITROVA LA LINEA

    comm.forward()
    time.sleep(TIME_STRAIGHT)

    cv2.imshow("Obstacle View", cleanImage)

    # RITORNA ALLO STATO LINEA UNA VOLTA FINITA LA MANOVRA
    
    print("MANOVRA COMPLETATA")
    return "LINE"