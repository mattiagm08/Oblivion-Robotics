import cv2 # type: ignore
import numpy as np # type: ignore
from picamera2 import Picamera2 #type: ignore
import serial # type: ignore

WINDOW_NAME_GREEN = "Immagine con sogliatura verde"
WINDOW_NAME_MAIN = "Main View"
WINDOW_NAME_MASK = "mask"
DEBUG_COLOR_RECT = (0, 255, 0)
DEBUG_THICKNESS = 2

GREEN_INITIAL_VALUES = [23, 69, 54, 82, 187, 255]

TOF_OBSTACLE_DISTANCE = 50

THRESHOLD_GRAY_LINE = 80
THRESHOLD_GRAY_CURVE = 40
GAUSSIAN_BLUR_KERN = (11, 11)
GAUSSIAN_BLUR_INTERSECTION = (15, 15)

MIN_GREEN_RECT_AREA = 26000
MAX_GREEN_PIXELS_TOTAL = 40000
MIN_LINE_CONTOUR_AREA = 500
MIN_TOP_LINE_AREA = 1000
TURN_180_GREEN_LIMIT = 40000

SCREEN_CENTER_X = 320
LEFT_THRESHOLD = 280
RIGHT_THRESHOLD = 360
DELTA_X_LIMIT = 40

ROI_TOP_CENTRAL = (0, 100, 640, 250)
ROI_LEFT_PANEL  = (0, 0, 100, 480)
ROI_RIGHT_PANEL = (540, 0, 640, 480)
ROI_BOTTOM      = (0, 380, 640, 480)
ROI_GAP_CHECK   = (0, 0, 640, 100)

k_p = 10
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)

lastCommand = None

def on_trackbar_change(value):
    pass

cv2.namedWindow(WINDOW_NAME_GREEN)
cv2.createTrackbar("H_min", WINDOW_NAME_GREEN, GREEN_INITIAL_VALUES[0], 179, on_trackbar_change)
cv2.createTrackbar("S_min", WINDOW_NAME_GREEN, GREEN_INITIAL_VALUES[1], 255, on_trackbar_change)
cv2.createTrackbar("V_min", WINDOW_NAME_GREEN, GREEN_INITIAL_VALUES[2], 255, on_trackbar_change)
cv2.createTrackbar("H_max", WINDOW_NAME_GREEN, GREEN_INITIAL_VALUES[3], 179, on_trackbar_change)
cv2.createTrackbar("S_max", WINDOW_NAME_GREEN, GREEN_INITIAL_VALUES[4], 255, on_trackbar_change)
cv2.createTrackbar("V_max", WINDOW_NAME_GREEN, GREEN_INITIAL_VALUES[5], 255, on_trackbar_change)

def invia_comando(comando):
    try:
        ser.write((comando + '\n').encode('utf-8'))
    except Exception as e:
        print(f"Errore seriale: {e}")

def sendIfChanged(cmdFunc, *args):
    global lastCommand
    key = (cmdFunc, args)
    if lastCommand != key:
        lastCommand = key
        cmdFunc(*args)

def general_begin():
    invia_comando("stop")

def forward(speed):
    invia_comando(f"avanti:{speed}")
    print("avanti/n")

def right(speed):
    invia_comando(f"destra:{speed}")
    print("destra/n")

def stop():
    invia_comando("stop")

def left(speed):
    invia_comando(f"sinistra:{speed}")
    print("sinistra/n")

def right_incr():
    invia_comando("incrociodx")

def left_incr():
    invia_comando("incrociosx")

def indietro():
    invia_comando("indietro")

def incr_180():
    invia_comando("inversione")

def rilascia():
    stop()
    ser.close()

def getSensors():
    try:
        while ser.in_waiting > 11:
            ser.read(1)
        if ser.in_waiting >= 11:
            import struct
            byte = ser.read(1)
            if byte == b'\xaa':
                payload = ser.read(10)
                if len(payload) == 10:
                    data = struct.unpack('<HHHf', payload)
                    return {
                        "tofFront": data[0],
                        "tofLeft":  data[1],
                        "tofRight": data[2],
                        "heading":  data[3]
                    }
    except Exception as e:
        print(f"Errore ricezione: {e}")
    return None

def getTrackbarValues():
    h_min = cv2.getTrackbarPos("H_min", WINDOW_NAME_GREEN)
    s_min = cv2.getTrackbarPos("S_min", WINDOW_NAME_GREEN)
    v_min = cv2.getTrackbarPos("V_min", WINDOW_NAME_GREEN)
    h_max = cv2.getTrackbarPos("H_max", WINDOW_NAME_GREEN)
    s_max = cv2.getTrackbarPos("S_max", WINDOW_NAME_GREEN)
    v_max = cv2.getTrackbarPos("V_max", WINDOW_NAME_GREEN)
    return np.array([h_min, s_min, v_min]), np.array([h_max, s_max, v_max])

def incr(img_pulita):
    curva = [0, 0]
    copia = img_pulita.copy()
    copia_verde = cv2.cvtColor(copia, cv2.COLOR_BGR2HSV)
    copia_verde = cv2.GaussianBlur(copia_verde, GAUSSIAN_BLUR_KERN, cv2.BORDER_REFLECT)
    copia = cv2.cvtColor(copia, cv2.COLOR_BGR2GRAY)
    copia = cv2.GaussianBlur(copia, GAUSSIAN_BLUR_INTERSECTION, cv2.BORDER_REFLECT)
    (_, copia) = cv2.threshold(copia, THRESHOLD_GRAY_LINE, 255, cv2.THRESH_BINARY_INV)

    cut_incr = copia_verde[0:480, 0:640]

    lower_green, upper_green = getTrackbarValues()
    mask = cv2.inRange(cut_incr, lower_green, upper_green)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    pixel_vv = cv2.countNonZero(mask)
    cv2.imshow(WINDOW_NAME_MASK, mask)

    start_cut = (0, 0)
    end_cut = (0, 0)

    if contours:
        green_contour = max(contours, key=cv2.contourArea)
        M = cv2.moments(green_contour)

        if M["m00"] != 0:
            center_x = int(M["m10"] / M["m00"])
            center_y = int(M["m01"] / M["m00"])
            cv2.circle(copia_verde, (center_x, center_y), 10, (0, 255, 0), -1)

            rect = cv2.minAreaRect(green_contour)
            box = cv2.boxPoints(rect)
            box = np.int8(box)

            second_rect_y = int(rect[0][1]) - int(rect[1][1] / 2)
            second_rect_x = int(rect[0][0]) - int(rect[1][0] / 2)
            second_rect_end_x = int(rect[0][0]) + int(rect[1][0] / 2)
            second_rect_end_y = int(rect[0][1]) + int(rect[1][1] / 2)

            cv2.rectangle(copia_verde, (second_rect_x, second_rect_y), (second_rect_end_x, second_rect_end_y), (255, 0, 0), 2)

            area_rettangolo = rect[1][0] * rect[1][1]

            if area_rettangolo > MIN_GREEN_RECT_AREA and pixel_vv < MAX_GREEN_PIXELS_TOTAL:
                curva = [0, 0]
                start_point1 = (second_rect_x, second_rect_y - 40)
                end_point1 = (second_rect_end_x, second_rect_y)
                cv2.rectangle(img_pulita, start_point1, end_point1, (255, 0, 0), 2)
                cut_sop = copia[start_point1[1]:end_point1[1], start_point1[0]:end_point1[0]]

                start_point2 = (second_rect_end_x, second_rect_y)
                end_point2 = (second_rect_end_x + 50, second_rect_end_y)
                cv2.rectangle(img_pulita, start_point2, end_point2, (255, 0, 0), 2)
                cut_latdx = copia[start_point2[1]:end_point2[1], start_point2[0]:end_point2[0]]

                bianchi_sop = cv2.countNonZero(cut_sop)
                neri_sop = cut_sop.size - bianchi_sop

                if bianchi_sop > neri_sop:
                    bianchi_latdx = cv2.countNonZero(cut_latdx)
                    neri_latdx = cut_latdx.size - bianchi_latdx

                    if bianchi_latdx > neri_latdx:
                        curva = [1, 0]
                        start_cut = (0, end_point1[1] - 50)
                        end_cut = (end_point1[0] + 100, 480)
                        cv2.rectangle(img_pulita, start_cut, end_cut, (0, 255, 0), 2)
                    elif bianchi_latdx < neri_latdx:
                        curva = [0, 1]
                        start_cut = (second_rect_x - 100, second_rect_y - 100)
                        end_cut = (640, 480)
                        cv2.rectangle(img_pulita, start_cut, end_cut, (0, 0, 255), 2)
                else:
                    curva = [0, 0]
            elif pixel_vv > MAX_GREEN_PIXELS_TOTAL:
                curva = [1, 1]

        cv2.imshow("pulita", img_pulita)

    if (curva[0] == 0 and curva[1] == 0) or (curva[0] == 1 and curva[1] == 1):
        return copia
    elif (curva[0] == 0 and curva[1] == 1) or (curva[0] == 1 and curva[1] == 0):
        img_black = np.zeros_like(copia)
        img_black[start_cut[1]:end_cut[1], start_cut[0]:end_cut[0]] = copia[start_cut[1]:end_cut[1], start_cut[0]:end_cut[0]]
        return img_black

def cur(img_pulita):
    curva = [0, 0]
    copia = img_pulita.copy()
    copia_verde = cv2.cvtColor(copia, cv2.COLOR_BGR2HSV)
    copia_verde = cv2.GaussianBlur(copia_verde, GAUSSIAN_BLUR_KERN, cv2.BORDER_REFLECT)
    copia = cv2.cvtColor(copia, cv2.COLOR_BGR2GRAY)
    copia = cv2.GaussianBlur(copia, GAUSSIAN_BLUR_KERN, cv2.BORDER_REFLECT)
    (_, copia) = cv2.threshold(copia, THRESHOLD_GRAY_CURVE, 255, cv2.THRESH_BINARY_INV)

    cut_incr = copia_verde[0:480, 0:640]

    lower_green, upper_green = getTrackbarValues()
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

            cv2.rectangle(copia_verde, (second_rect_x, second_rect_y), (second_rect_end_x, second_rect_end_y), (255, 0, 0), 2)

            area_rettangolo = rect[1][0] * rect[1][1]
            if area_rettangolo > MIN_GREEN_RECT_AREA:
                start_point1 = (second_rect_x, second_rect_y - 40)
                end_point1 = (second_rect_end_x, second_rect_y)
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
                        if pixel_vv < MAX_GREEN_PIXELS_TOTAL:
                            curva = [1, 0]
                        elif pixel_vv > MAX_GREEN_PIXELS_TOTAL:
                            start_cut2 = (0, second_rect_y - 40)
                            end_cut2 = (640, 480)
                            cut_180 = mask[start_cut2[1]:end_cut2[1], start_cut2[0]:end_cut2[0]]
                            pixel_vv_180 = cv2.countNonZero(cut_180)
                            if pixel_vv_180 > TURN_180_GREEN_LIMIT:
                                curva = [1, 1]
                            else:
                                curva = [1, 0]
                    elif bianchi_latdx < neri_latdx:
                        if pixel_vv < MAX_GREEN_PIXELS_TOTAL:
                            curva = [0, 1]
                        elif pixel_vv > MAX_GREEN_PIXELS_TOTAL:
                            start_cut2 = (0, second_rect_y - 40)
                            end_cut2 = (640, 480)
                            cut_180 = mask[start_cut2[1]:end_cut2[1], start_cut2[0]:end_cut2[0]]
                            pixel_vv_180 = cv2.countNonZero(cut_180)
                            if pixel_vv_180 > TURN_180_GREEN_LIMIT:
                                curva = [1, 1]
                            else:
                                curva = [0, 1]
                else:
                    curva = [0, 0]
    return curva

picam2 = Picamera2()

def main():
    global lastCommand
    general_begin()
    try:
        picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (600, 800)}))
        picam2.start()
    except Exception as e:
        print(f"Errore telecamera: {e}")

    vel = 94

    while True:
        try:
            img_pulita = picam2.capture_array()
            img_pulita = cv2.rotate(img_pulita, cv2.ROTATE_90_COUNTERCLOCKWISE)
        except:
            break

        sensorData = getSensors()
        if sensorData and sensorData['tofFront'] < TOF_OBSTACLE_DISTANCE:
            sendIfChanged(stop)
            cv2.imshow(WINDOW_NAME_MAIN, img_pulita)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                rilascia()
                break
            continue
        
        cropX = (800 - 640) // 2
        cropY = (600 - 480) // 2
        img_pulita = img_pulita[cropY:cropY + 480, cropX:cropX + 640]

        copia_pulita = img_pulita.copy()
        line = incr(img_pulita)
        copia = line.copy()

        cv2.imshow(WINDOW_NAME_MAIN, img_pulita)

        sp  = ROI_TOP_CENTRAL;  ep  = (ROI_TOP_CENTRAL[2],  ROI_TOP_CENTRAL[3])
        sp2 = ROI_LEFT_PANEL;   ep2 = (ROI_LEFT_PANEL[2],   ROI_LEFT_PANEL[3])
        sp3 = ROI_RIGHT_PANEL;  ep3 = (ROI_RIGHT_PANEL[2],  ROI_RIGHT_PANEL[3])
        sp4 = ROI_BOTTOM;       ep4 = (ROI_BOTTOM[2],       ROI_BOTTOM[3])
        sp5 = ROI_GAP_CHECK;    ep5 = (ROI_GAP_CHECK[2],    ROI_GAP_CHECK[3])

        cv2.rectangle(copia, (sp[0],  sp[1]),  ep,  DEBUG_COLOR_RECT, DEBUG_THICKNESS)
        cv2.rectangle(copia, (sp2[0], sp2[1]), ep2, DEBUG_COLOR_RECT, DEBUG_THICKNESS)
        cv2.rectangle(copia, (sp3[0], sp3[1]), ep3, DEBUG_COLOR_RECT, DEBUG_THICKNESS)
        cv2.rectangle(copia, (sp4[0], sp4[1]), ep4, DEBUG_COLOR_RECT, DEBUG_THICKNESS)
        cv2.rectangle(copia, (sp5[0], sp5[1]), ep5, DEBUG_COLOR_RECT, DEBUG_THICKNESS)

        cut_sopra = copia[sp[1]:ep[1],   sp[0]:ep[0]]
        cut_dx    = copia[sp2[1]:ep2[1], sp2[0]:ep2[0]]
        cut_sx    = copia[sp3[1]:ep3[1], sp3[0]:ep3[0]]
        cut_sotto = copia[sp4[1]:ep4[1], sp4[0]:ep4[0]]
        cut_gap   = copia[sp5[1]:ep5[1], sp5[0]:ep5[0]]

        contours_sopra, _ = cv2.findContours(cut_sopra, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours_dx,    _ = cv2.findContours(cut_dx,    cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours_sx,    _ = cv2.findContours(cut_sx,    cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        filtered_contours_sopra = [cnt for cnt in contours_sopra if cv2.contourArea(cnt) > MIN_LINE_CONTOUR_AREA]
        filtered_contours_dx    = [cnt for cnt in contours_dx    if cv2.contourArea(cnt) > MIN_LINE_CONTOUR_AREA]
        filtered_contours_sx    = [cnt for cnt in contours_sx    if cv2.contourArea(cnt) > MIN_LINE_CONTOUR_AREA]

        M      = cv2.moments(cut_sopra)
        Msotto = cv2.moments(cut_sotto)
        Mgap   = cv2.moments(cut_gap)

        centro_sopra = [int(M["m10"]/M["m00"]),           int(M["m01"]/M["m00"]) + ROI_TOP_CENTRAL[1]] if M["m00"] != 0 else [0, 0]
        centro_sotto = [int(Msotto["m10"]/Msotto["m00"]) + ROI_BOTTOM[0],    int(Msotto["m01"]/Msotto["m00"])]    if Msotto["m00"] != 0 else [0, 0]
        centro_gap   = [int(Mgap["m10"]/Mgap["m00"])     + ROI_GAP_CHECK[0], int(Mgap["m01"]/Mgap["m00"])]        if Mgap["m00"] != 0 else [0, 0]

        delta_x    = centro_sotto[0] - centro_gap[0]
        area_sopra = sum(cv2.contourArea(c) for c in filtered_contours_sopra)

        if area_sopra > MIN_TOP_LINE_AREA:
            curva = cur(copia_pulita)

            if curva[0] == 0 and curva[1] == 0:
                if centro_sopra[0] == 0:
                    sendIfChanged(stop)
                elif (LEFT_THRESHOLD <= centro_sopra[0] <= RIGHT_THRESHOLD) or (-DELTA_X_LIMIT < delta_x < DELTA_X_LIMIT):
                    sendIfChanged(forward, vel)
                elif centro_sopra[0] < LEFT_THRESHOLD:
                    sendIfChanged(left, vel)
                elif centro_sopra[0] > RIGHT_THRESHOLD:
                    sendIfChanged(right, vel)
            elif curva[0] == 1 and curva[1] == 0:
                sendIfChanged(left_incr)
                print("INCROCIOsx")
            elif curva[0] == 0 and curva[1] == 1:
                sendIfChanged(right_incr)
                print("INCROCIOdx")
            elif curva[0] == 1 and curva[1] == 1:
                sendIfChanged(incr_180)
                print("INCROCIO 180")
        else:
            area_dx = sum(cv2.contourArea(c) for c in filtered_contours_dx)
            area_sx = sum(cv2.contourArea(c) for c in filtered_contours_sx)
            if area_dx > area_sx:
                sendIfChanged(left, vel)
            elif area_sx > area_dx:
                sendIfChanged(right, vel)

        cv2.imshow("line", line)
        cv2.imshow("copia", copia)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            rilascia()
            break

    picam2.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
