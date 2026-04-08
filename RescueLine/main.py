# LIBRERIE E STATI IMPORTATI

import config
import comm
import cv2 # type: ignore
from picamera2 import Picamera2 # type: ignore
from states import line_follower, rescue_zone, obstacle

def main():

    # INIZIALIZZAZIONE COMUNICAZIONE

    comm.begin()
    line_follower.initTrackbars() 

    # SETUP PICAMERA

    piCam = Picamera2()

    try:
        # CONFIGURAZIONE E AVVIO PICAMERA

        piCam.configure(piCam.create_preview_configuration(main={"format": 'XRGB8888', "size": (800, 600)}))
        piCam.start()

    # ERRORE PICAMERA AVVIO

    except Exception as e:
        print(f"Camera error: {e}")

    # INIZIALIZZAZIONE STATO CORRENTE

    currentState = "LINE"

    # CATTURA FRAME

    while True:
        try:
            cleanImage = piCam.capture_array()
            cleanImage = cv2.rotate(cleanImage, cv2.ROTATE_90_CLOCKWISE)
        except:
            break     

        # LOGICA STATE MACHINE

        match currentState:        

            case "LINE":
                currentState = line_follower.run(cleanImage)

            case "RESCUE":
                currentState = rescue_zone.run(cleanImage)

            case "OBSTACLE":
                currentState = obstacle.run(cleanImage)

            case _:
                currentState = "LINE"

        # CHIUSURA CON EXIT KEY ('q') E RILASCIO RISORSE

        if cv2.waitKey(1) & 0xFF == ord('q'):
            comm.release()
            break

    # STOP PICAMERA E CHIUSURA FINESTRE

    piCam.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":

    main()