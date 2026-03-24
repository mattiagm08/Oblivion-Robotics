import cv2 # type: ignore
import numpy as np # type: ignore
from picamera2 import Picamera2 #type: ignore
import time # type: ignore
import serial # type: ignore

k_p = 10  # Increased Proportional control gain
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)

def on_trackbar_change(value):
    pass

vel_dx = 80
vel_sx = 80

def general_begin():
    # Sistema tutti i servo o invia segnale di avvio
    invia_comando("START")

def invia_comando(comando):
    """Funzione di supporto per inviare i dati via seriale"""
    try:
        ser.write((comando + '\n').encode('utf-8'))
    except Exception as e:
        print(f"Errore seriale: {e}")

cor = 15
        
# Funzioni di movimento con invio seriale
def forward(speed):
    invia_comando(f"avanti:{speed}")
   
def avanti():
    invia_comando("avanti")

def right(speed, stato=None):
    invia_comando(f"destra:{speed}")

def stop():
    invia_comando("stop")

def left(speed, stato=None):
    invia_comando(f"sinistra:{speed}")
    
def right_incr():
    invia_comando("incrociodx")
    
def left_incr():
    invia_comando("incrociosx")

def indietro():
    invia_comando("indietro")

def incr_180():
    invia_comando("inversione")

window_name = "Immagine con sogliatura verde"
cv2.namedWindow(window_name)
initial_values = [23, 69, 54, 82, 187, 255]
cv2.createTrackbar("H_min", window_name, initial_values[0], 179, on_trackbar_change)
cv2.createTrackbar("S_min", window_name, initial_values[1], 255, on_trackbar_change)
cv2.createTrackbar("V_min", window_name, initial_values[2], 255, on_trackbar_change)
cv2.createTrackbar("H_max", window_name, initial_values[3], 179, on_trackbar_change)
cv2.createTrackbar("S_max", window_name, initial_values[4], 255, on_trackbar_change)
cv2.createTrackbar("V_max", window_name, initial_values[5], 255, on_trackbar_change)

def incr(img_pulita):
    curva = (0, 0)
    copia = img_pulita.copy()
    copia_verde = cv2.cvtColor(copia, cv2.COLOR_BGR2HSV)
    copia_verde = cv2.GaussianBlur(copia_verde, (5, 5), cv2.BORDER_REFLECT)
    copia = cv2.cvtColor(copia, cv2.COLOR_BGR2GRAY)
    copia = cv2.GaussianBlur(copia, (15, 15), cv2.BORDER_REFLECT)
    (_, copia) = cv2.threshold(copia, 120, 255, cv2.THRESH_BINARY_INV)
   
    start_point5 = (0, 0)
    end_point5 = (640, 480)
    cut_incr = copia_verde[start_point5[1]:end_point5[1], start_point5[0]:end_point5[0]]
   
    H_min = cv2.getTrackbarPos("H_min", window_name)
    S_min = cv2.getTrackbarPos("S_min", window_name)
    V_min = cv2.getTrackbarPos("V_min", window_name)
    H_max = cv2.getTrackbarPos("H_max", window_name)
    S_max = cv2.getTrackbarPos("S_max", window_name)
    V_max = cv2.getTrackbarPos("V_max", window_name)

    lower_green = np.array([H_min, S_min, V_min])
    upper_green = np.array([H_max, S_max, V_max])

    mask = cv2.inRange(cut_incr, lower_green, upper_green)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    pixel_vv = cv2.countNonZero(mask)
    cv2.imshow("mask", mask )
    if contours:
        green_contour = max(contours, key=cv2.contourArea)
        M = cv2.moments(green_contour)
       
        if M["m00"] != 0:
            center_x = int(M["m10"] / M["m00"])
            center_y = int(M["m01"] / M["m00"])
            center_y = center_y + 0
            cv2.circle(copia_verde, (center_x, center_y), 10, (0, 255, 0), -1)
           
            rect = cv2.minAreaRect(green_contour)
            box = cv2.boxPoints(rect)
            box = np.int8(box)

            second_rect_y = int(rect[0][1]) - int(rect[1][1] / 2)
            second_rect_x = int(rect[0][0]) - int(rect[1][0] / 2)
            second_rect_end_x = int(rect[0][0]) + int(rect[1][0] / 2)
            second_rect_end_y = int(rect[0][1]) + int(rect[1][1] / 2)
           
            cv2.rectangle(copia_verde, (second_rect_x, second_rect_y ), (second_rect_end_x, second_rect_end_y ), (255, 0, 0), 2)

            area_rettangolo = rect[1][0] * rect[1][1]
            if area_rettangolo > 26000 and pixel_vv < 40000:
               
                curva = [0, 0]
                start_point1 = (second_rect_x, second_rect_y -40 )
                end_point1 = (second_rect_end_x, second_rect_y )
                cv2.rectangle(img_pulita, start_point1, end_point1, (255, 0, 0), 2)
                cut_sop = copia[start_point1[1]:end_point1[1], start_point1[0]:end_point1[0]]
               
                start_point2 = (second_rect_end_x, second_rect_y)
                end_point2 = (second_rect_end_x + 50, second_rect_end_y)
                cv2.rectangle(img_pulita, start_point2, end_point2, (255, 0, 0), 2)
                cut_latdx = copia[start_point2[1]:end_point2[1], start_point2[0]:end_point2[0]]
               
                bianchi_sop = cv2.countNonZero(cut_sop)
                neri_sop = cut_sop.size - bianchi_sop
               
                if bianchi_sop > neri_sop:
                    #print("incrocio valido")
                    bianchi_latdx = cv2.countNonZero(cut_latdx)
                    neri_latdx = cut_latdx.size - bianchi_latdx
                   
                    if bianchi_latdx > neri_latdx:
                        curva = [1, 0]
                        start_cut = (0, end_point1[1]-50)
                        end_cut = (end_point1[0]+100, 480)
                        cv2.rectangle(img_pulita,start_cut,end_cut,(0,255,0),2)
                       
                    elif bianchi_latdx < neri_latdx:
                        curva = [0, 1]
                        start_cut=(second_rect_x-100,second_rect_y-100)
                        end_cut=(640,480)
                        cv2.rectangle(img_pulita,start_cut,end_cut,(0,0,255),2)
                else:
                    curva = [0, 0]
            elif pixel_vv > 40000:
                     curva = [1,1]
            cv2.imshow("pulita",img_pulita)
    if curva[0] == 0 and curva[1] == 0 or curva[0] == 1 and curva[1]==1:
        return copia
    elif curva[0] == 0 and curva[1] == 1 or curva[0] == 1 and curva[1] == 0:
        img_black = np.zeros_like(copia)
        img_black[start_cut[1]:end_cut[1], start_cut[0]:end_cut[0]] = copia[start_cut[1]:end_cut[1], start_cut[0]:end_cut[0]]
        return img_black

def cur(img_pulita):
    curva = (0,0)
    copia = img_pulita.copy()
    copia_verde = cv2.cvtColor(copia, cv2.COLOR_BGR2HSV)
    copia_verde = cv2.GaussianBlur(copia_verde, (5, 5), cv2.BORDER_REFLECT)
    copia = cv2.cvtColor(copia, cv2.COLOR_BGR2GRAY)
    copia = cv2.GaussianBlur(copia, (5, 5), cv2.BORDER_REFLECT)
    (_, copia) = cv2.threshold(copia, 90, 255, cv2.THRESH_BINARY_INV)
   
    start_point5 = (0, 0)
    end_point5 = (640, 480)
    cut_incr = copia_verde[start_point5[1]:end_point5[1], start_point5[0]:end_point5[0]]
   
    H_min = cv2.getTrackbarPos("H_min", window_name)
    S_min = cv2.getTrackbarPos("S_min", window_name)
    V_min = cv2.getTrackbarPos("V_min", window_name)
    H_max = cv2.getTrackbarPos("H_max", window_name)
    S_max = cv2.getTrackbarPos("S_max", window_name)
    V_max = cv2.getTrackbarPos("V_max", window_name)

    lower_green = np.array([H_min, S_min, V_min])
    upper_green = np.array([H_max, S_max, V_max])

    mask = cv2.inRange(cut_incr, lower_green, upper_green)
    pixel_vv = cv2.countNonZero(mask)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        green_contour = max(contours, key=cv2.contourArea)
        M = cv2.moments(green_contour)
       
        if M["m00"] != 0:
            center_x = int(M["m10"] / M["m00"])
            center_y = int(M["m01"] / M["m00"])
            cv2.circle(copia_verde, (center_x, center_y), 10, (0, 255, 0), -1)
           
            rect = cv2.minAreaRect(green_contour)
            second_rect_y = int(rect[0][1]) - int(rect[1][1] / 2)
            second_rect_x = int(rect[0][0]) - int(rect[1][0] / 2)
            second_rect_end_x = int(rect[0][0]) + int(rect[1][0] / 2)
            second_rect_end_y = int(rect[0][1]) + int(rect[1][1] / 2)
           
            cv2.rectangle(copia_verde, (second_rect_x, second_rect_y ), (second_rect_end_x, second_rect_end_y ), (255, 0, 0), 2)

            area_rettangolo = rect[1][0] * rect[1][1]
            if area_rettangolo > 26000:
                start_point1 = (second_rect_x, second_rect_y -40 )
                end_point1 = (second_rect_end_x, second_rect_y )
                cut_sop = copia[start_point1[1]:end_point1[1], start_point1[0]:end_point1[0]]
               
                start_point2 = (second_rect_end_x, second_rect_y)
                end_point2 = (second_rect_end_x + 50, second_rect_end_y)
                cut_latdx = copia[start_point2[1]:end_point2[1], start_point2[0]:end_point2[0]]
               
                bianchi_sop = cv2.countNonZero(cut_sop)
                neri_sop = cut_sop.size - bianchi_sop
               
                if bianchi_sop > neri_sop:
                    bianchi_latdx = cv2.countNonZero(cut_latdx)
                    neri_latdx = cut_latdx.size - bianchi_latdx
                   
                    if bianchi_latdx > neri_latdx:
                        if (pixel_vv < 40000):
                            curva = [1, 0]
                        elif(pixel_vv > 40000):
                            start_cut2 = (0,second_rect_y -40)
                            end_cut2 = (640,480)
                            cut_180 = mask[start_cut2[1]:end_cut2[1], start_cut2[0]:end_cut2[0]]
                            pixel_vv = cv2.countNonZero(cut_180)
                            if(pixel_vv > 50000):
                                curva = [1,1]
                            else:
                                curva = [1,0]
                    elif bianchi_latdx < neri_latdx:
                        if (pixel_vv < 40000):
                            curva = [0, 1]
                        elif(pixel_vv > 40000):
                            start_cut2 = (0,second_rect_y -40)
                            end_cut2 = (640,480)
                            cut_180 = mask[start_cut2[1]:end_cut2[1], start_cut2[0]:end_cut2[0]]
                            pixel_vv = cv2.countNonZero(cut_180)
                            if(pixel_vv > 40000):
                                curva = [1,1]
                            else:
                                curva = [0,1]
                else:
                    curva = [0, 0]
    return curva

def validate(frame):
    return 0

def rilascia():
    # Invia stop e chiudi seriale
    stop()
    ser.close()

picam2 = Picamera2()

def main():
    general_begin()
    try:
        picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
        picam2.start()
    except Exception as e:
        print(f"Errore telecamera: {e}")

    while True:
        try:
            img_pulita = picam2.capture_array()
        except:
            break
        
        copia_pulita = img_pulita.copy()
        line = incr(img_pulita)
        copia = line.copy()
        
        cv2.imshow("ciao",img_pulita)
        
        vel=94
        start_point = (0, 100); end_point = (640, 250)
        start_point2 = (0, 0); end_point2 = (100, 480)
        start_point3 = (540, 0); end_point3 = (640, 480)
        start_point4 = (0, 380); end_point4 = (640, 480)
        start_point5 = (0, 0); end_point5 = (640, 100)
        
        color = (0, 255, 0); thickness = 2
        cv2.rectangle(copia, start_point, end_point, color, thickness)
        cv2.rectangle(copia, start_point2, end_point2, color, thickness)
        cv2.rectangle(copia, start_point3, end_point3, color, thickness)
        cv2.rectangle(copia, start_point4, end_point4, color, thickness)
        cv2.rectangle(copia, start_point5, end_point5, color, thickness)
        
        cut_sopra = copia[start_point[1]:end_point[1], start_point[0]:end_point[0]]
        cut_dx = copia[start_point2[1]:end_point2[1], start_point2[0]:end_point2[0]]
        cut_sx = copia[start_point3[1]:end_point3[1], start_point3[0]:end_point3[0]]
        cut_sotto = copia[start_point4[1]:end_point4[1], start_point4[0]:end_point4[0]]
        cut_gap = copia[start_point5[1]:end_point5[1], start_point5[0]:end_point5[0]]
        
        contours_sopra, _ = cv2.findContours(cut_sopra, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours_dx, _ = cv2.findContours(cut_dx, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours_sx, _ = cv2.findContours(cut_sx, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours_sotto, _ = cv2.findContours(cut_sotto, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours_gap, _ = cv2.findContours(cut_gap, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        min_area = 500
        filtered_contours_sopra = [cnt for cnt in contours_sopra if cv2.contourArea(cnt) > min_area]
        filtered_contours_dx = [cnt for cnt in contours_dx if cv2.contourArea(cnt) > min_area]
        filtered_contours_sx = [cnt for cnt in contours_sx if cv2.contourArea(cnt) > min_area]
        
        M = cv2.moments(cut_sopra)
        Msotto = cv2.moments(cut_sotto)
        Mgap = cv2.moments(cut_gap)
        
        centro_sopra = [int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"]) + 150] if M["m00"] != 0 else [0,0]
        centro_sotto = [int(Msotto["m10"]/Msotto["m00"]) + 540, int(Msotto["m01"]/Msotto["m00"])] if Msotto["m00"] != 0 else [0,0]
        centro_gap = [int(Mgap["m10"]/Mgap["m00"]) + 540, int(Mgap["m01"]/Mgap["m00"])] if Mgap["m00"] != 0 else [0,0]
        
        delta_x = centro_sotto[0] - centro_gap[0]
        area_sopra = sum(cv2.contourArea(c) for c in filtered_contours_sopra)
        
        if area_sopra > 1000:
            curva = cur(copia_pulita)
            if curva[0] == 0 and curva[1] == 0:
                 if (280 < centro_sopra[0] < 360) or (-40 < delta_x < 40):
                    forward(vel)
                 elif centro_sopra[0] < 300:
                    left(vel)
                 elif centro_sopra[0] > 340:
                    right(vel)
            elif curva[0] == 1 and curva[1] == 0:
                left_incr()
                print("INCROCIOsx")
            elif curva[0] == 0 and curva[1] == 1:
                left_incr()
                print("INCROCIOdx")
            elif curva[0] == 1 and curva[1] == 1:
                incr_180()
                print("INCROCIO 180")
        else:
            area_dx = sum(cv2.contourArea(c) for c in filtered_contours_dx)
            area_sx = sum(cv2.contourArea(c) for c in filtered_contours_sx)
            if area_dx > area_sx: left(vel)
            elif area_sx > area_dx: right(vel)

        cv2.imshow("line", line)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            rilascia()
            break

    picam2.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
