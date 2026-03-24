import cv2 # type: ignore
from picamera2 import Picamera2 # type: ignore
import config
import comm
from states import line_follower, rescue_zone

def main():
    comm.general_begin()
    config.init_trackbars()
    
    picam2 = Picamera2()
    try:
        picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
        picam2.start()
    except Exception as e:
        print(f"Errore telecamera: {e}")

    current_state = "LINE"

    while True:
        try:
            img_pulita = picam2.capture_array()
        except:
            break
        
        if current_state == "LINE":
            current_state = line_follower.run(img_pulita)
        elif current_state == "RESCUE":
            current_state = rescue_zone.run(img_pulita)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            comm.rilascia()
            break

    picam2.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()