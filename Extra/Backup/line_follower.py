import cv2
import numpy as np  # type: ignore
import comm # type: ignore
import subprocess

#modified

WINDOW_NAME_GREEN = "Immagine con sogliatura verde"
WINDOW_NAME_MAIN  = "Main View"
WINDOW_NAME_MASK  = "mask"
DEBUG_COLOR_RECT  = (0, 255, 0)
DEBUG_THICKNESS   = 2

GREEN_INITIAL_VALUES = [10, 108, 29, 85, 235, 255]

TOF_OBSTACLE_DISTANCE = 50
THRESHOLD_GRAY_LINE = 80
THRESHOLD_GRAY_CURVE = 90
GAUSSIAN_BLUR_KERN = (11, 11)
GAUSSIAN_BLUR_INTERSECTION = (15, 15)

MIN_GREEN_RECT_AREA = 15000
MAX_GREEN_PIXELS_TOTAL = 120000
MIN_GREEN_PIXELS_SIDE = 2000
MIN_LINE_CONTOUR_AREA = 500
MIN_TOP_LINE_AREA = 1000
TURN_180_GREEN = 5000

SCREEN_CENTER_X = 320
LEFT_THRESHOLD = 280
RIGHT_THRESHOLD = 360
DELTA_X_LIMIT = 40

GREEN_ROI_Y_START = 150
GREEN_ROI_Y_END = 400
GREEN_CENTER_OFFSET = 20

VV_RIGHT_PANEL   = (600, 100, 800, 500)
VV_LEFT_PANEL    = (0,   100, 200, 500)
ROI_TOP_CENTRAL = (0, 100, 640, 250)
ROI_LEFT_PANEL   = (0,   0, 100, 480)
ROI_RIGHT_PANEL = (540,  0, 640, 480)
ROI_BOTTOM       = (0, 380, 640, 480)
ROI_GAP_CHECK    = (0,   0, 640, 100)

_lastCommand = None



def _onTrackbarChange(_value):
    h_min = cv2.getTrackbarPos("H_min", WINDOW_NAME_GREEN)
    s_min = cv2.getTrackbarPos("S_min", WINDOW_NAME_GREEN)
    v_min = cv2.getTrackbarPos("V_min", WINDOW_NAME_GREEN)
    h_max = cv2.getTrackbarPos("H_max", WINDOW_NAME_GREEN)
    s_max = cv2.getTrackbarPos("S_max", WINDOW_NAME_GREEN)
    v_max = cv2.getTrackbarPos("V_max", WINDOW_NAME_GREEN)
    print(f"HSV ? lower: [{h_min}, {s_min}, {v_min}]  upper: [{h_max}, {s_max}, {v_max}]")

def initTrackbars():
    cv2.namedWindow(WINDOW_NAME_GREEN)
    cv2.createTrackbar("H_min", WINDOW_NAME_GREEN, GREEN_INITIAL_VALUES[0],  64, _onTrackbarChange)
    cv2.createTrackbar("S_min", WINDOW_NAME_GREEN, GREEN_INITIAL_VALUES[1], 127, _onTrackbarChange)
    cv2.createTrackbar("V_min", WINDOW_NAME_GREEN, GREEN_INITIAL_VALUES[2],  55, _onTrackbarChange)
    cv2.createTrackbar("H_max", WINDOW_NAME_GREEN, GREEN_INITIAL_VALUES[3], 135, _onTrackbarChange)
    cv2.createTrackbar("S_max", WINDOW_NAME_GREEN, GREEN_INITIAL_VALUES[4], 235, _onTrackbarChange)
    cv2.createTrackbar("V_max", WINDOW_NAME_GREEN, GREEN_INITIAL_VALUES[5], 255, _onTrackbarChange)

def _getTrackbarValues():
    h_min = cv2.getTrackbarPos("H_min", WINDOW_NAME_GREEN)
    s_min = cv2.getTrackbarPos("S_min", WINDOW_NAME_GREEN)
    v_min = cv2.getTrackbarPos("V_min", WINDOW_NAME_GREEN)
    h_max = cv2.getTrackbarPos("H_max", WINDOW_NAME_GREEN)
    s_max = cv2.getTrackbarPos("S_max", WINDOW_NAME_GREEN)
    v_max = cv2.getTrackbarPos("V_max", WINDOW_NAME_GREEN)
    return np.array([h_min, s_min, v_min]), np.array([h_max, s_max, v_max])

def _sendIfChanged(cmdFunc):
    global _lastCommand
    if _lastCommand != cmdFunc:
        _lastCommand = cmdFunc
        cmdFunc()

def _incr(img_pulita, img_nocrop):
    gray = cv2.cvtColor(img_pulita, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, GAUSSIAN_BLUR_INTERSECTION, cv2.BORDER_REFLECT)
    _, binary = cv2.threshold(gray, THRESHOLD_GRAY_LINE, 255, cv2.THRESH_BINARY_INV)
    return binary

def run(cleanImage):       
        
    sensorData = comm.getSensors()
    if sensorData and sensorData['tofFront'] < TOF_OBSTACLE_DISTANCE:
        _sendIfChanged(comm.stop)
        cv2.imshow(WINDOW_NAME_MAIN, cleanImage)
        return "LINE"

    img_senza_crop = cleanImage.copy()
    copia_pulita   = cleanImage.copy()
    cropX = (800 - 640) // 2
    cropY = (600 - 480) // 2
    copia_pulita = copia_pulita[cropY:cropY + 480, cropX:cropX + 640]

    line = _incr(copia_pulita, img_senza_crop)
    copia = line.copy()

    cv2.imshow(WINDOW_NAME_MAIN, cleanImage)

    sp  = ROI_TOP_CENTRAL; ep  = (ROI_TOP_CENTRAL[2], ROI_TOP_CENTRAL[3])
    sp2 = ROI_LEFT_PANEL; ep2 = (ROI_LEFT_PANEL[2], ROI_LEFT_PANEL[3])
    sp3 = ROI_RIGHT_PANEL; ep3 = (ROI_RIGHT_PANEL[2], ROI_RIGHT_PANEL[3])
    sp4 = ROI_BOTTOM; ep4 = (ROI_BOTTOM[2], ROI_BOTTOM[3])
    sp5 = ROI_GAP_CHECK; ep5 = (ROI_GAP_CHECK[2], ROI_GAP_CHECK[3])

    cv2.rectangle(copia, (sp[0],  sp[1]),  ep,  DEBUG_COLOR_RECT, DEBUG_THICKNESS)
    cv2.rectangle(copia, (sp2[0], sp2[1]), ep2, DEBUG_COLOR_RECT, DEBUG_THICKNESS)
    cv2.rectangle(copia, (sp3[0], sp3[1]), ep3, DEBUG_COLOR_RECT, DEBUG_THICKNESS)
    cv2.rectangle(copia, (sp4[0], sp4[1]), ep4, DEBUG_COLOR_RECT, DEBUG_THICKNESS)
    cv2.rectangle(copia, (sp5[0], sp5[1]), ep5, DEBUG_COLOR_RECT, DEBUG_THICKNESS)

    cut_sopra = copia[sp[1]:ep[1], sp[0]:ep[0]]
    cut_dx = copia[sp2[1]:ep2[1], sp2[0]:ep2[0]]
    cut_sx = copia[sp3[1]:ep3[1], sp3[0]:ep3[0]]
    cut_sotto = copia[sp4[1]:ep4[1], sp4[0]:ep4[0]]
    cut_gap = copia[sp5[1]:ep5[1], sp5[0]:ep5[0]]

    contours_sopra, _ = cv2.findContours(cut_sopra, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_dx, _ = cv2.findContours(cut_dx, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_sx, _ = cv2.findContours(cut_sx, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    filtered_contours_sopra = [cnt for cnt in contours_sopra if cv2.contourArea(cnt) > MIN_LINE_CONTOUR_AREA]
    filtered_contours_dx = [cnt for cnt in contours_dx if cv2.contourArea(cnt) > MIN_LINE_CONTOUR_AREA]
    filtered_contours_sx = [cnt for cnt in contours_sx if cv2.contourArea(cnt) > MIN_LINE_CONTOUR_AREA]

    M = cv2.moments(cut_sopra)
    Msotto = cv2.moments(cut_sotto)
    Mgap = cv2.moments(cut_gap)

    centro_sopra = [int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]) + ROI_TOP_CENTRAL[1]] if M["m00"] != 0 else [0, 0]
    centro_sotto = [int(Msotto["m10"] / Msotto["m00"]) + ROI_BOTTOM[0], int(Msotto["m01"] / Msotto["m00"])] if Msotto["m00"] != 0 else [0, 0]
    centro_gap = [int(Mgap["m10"] / Mgap["m00"]) + ROI_GAP_CHECK[0], int(Mgap["m01"] / Mgap["m00"])] if Mgap["m00"] != 0 else [0, 0]

    gray = cv2.cvtColor(copia_pulita, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, GAUSSIAN_BLUR_INTERSECTION, cv2.BORDER_REFLECT)
    _, binary_line = cv2.threshold(gray, THRESHOLD_GRAY_LINE, 255, cv2.THRESH_BINARY_INV)

    delta_x = centro_sotto[0] - centro_gap[0]
    cut_sopra_line = binary_line[ROI_TOP_CENTRAL[1]:ROI_TOP_CENTRAL[3], ROI_TOP_CENTRAL[0]:ROI_TOP_CENTRAL[2]]
    area_sopra = cv2.countNonZero(cut_sopra_line)

    if area_sopra > MIN_TOP_LINE_AREA:
        if centro_sopra[0] == 0:
            _sendIfChanged(comm.stop)
        else:
            hsv = cv2.cvtColor(copia_pulita, cv2.COLOR_BGR2HSV)
            lower_green, upper_green = _getTrackbarValues()
            mask_green = cv2.inRange(hsv, lower_green, upper_green)
            x_c = centro_sopra[0]
            
            M_green = cv2.moments(mask_green)
            
            area_rettangolo = M_green["m00"] if M_green["m00"] != 0 else 0
    
            if M_green["m00"] != 0:
                cx_green = int(M_green["m10"] / M_green["m00"])
                cy_green = int(M_green["m01"] / M_green["m00"])
            else:
                cx_green, cy_green = 0, 0
                            
            RECT_W = 60
            RECT_H = 40
            OFFSET_Y = 200

            x1 = max(0, cx_green - RECT_W // 2)
            x2 = min(640, cx_green + RECT_W // 2)
            y1 = max(0, cy_green - OFFSET_Y - RECT_H)
            y2 = max(0, cy_green - OFFSET_Y)

            cv2.rectangle(
                copia_pulita,
                (x1, y1),
                (x2, y2),
                (0, 0, 255),  # rosso
                2
            )
                        
            roi_check = binary_line[y1:y2, x1:x2]

            pixel_bianchi = cv2.countNonZero(roi_check)
            area_roi = roi_check.shape[0] * roi_check.shape[1]
                
            pixel_neri = area_roi - pixel_bianchi

                        
            roi_sx = mask_green[GREEN_ROI_Y_START:GREEN_ROI_Y_END, 0:max(0, x_c - GREEN_CENTER_OFFSET)]
            roi_dx = mask_green[GREEN_ROI_Y_START:GREEN_ROI_Y_END, min(640, x_c + GREEN_CENTER_OFFSET):640]
            pixel_sx = cv2.countNonZero(roi_sx)
            pixel_dx = cv2.countNonZero(roi_dx)
                        
                        # ROI statiche sulla mask verde
            roi_sx_statico = mask_green[ROI_LEFT_PANEL[1]:ROI_LEFT_PANEL[3],
                            ROI_LEFT_PANEL[0]:ROI_LEFT_PANEL[2]]

            roi_dx_statico = mask_green[ROI_RIGHT_PANEL[1]:ROI_RIGHT_PANEL[3],
                            ROI_RIGHT_PANEL[0]:ROI_RIGHT_PANEL[2]]

            # Conteggio pixel verdi
            pixel_sx_statico = cv2.countNonZero(roi_sx_statico)
            pixel_dx_statico = cv2.countNonZero(roi_dx_statico)
            
            if pixel_sx_statico > TURN_180_GREEN and pixel_dx_statico > TURN_180_GREEN and area_rettangolo > MIN_GREEN_RECT_AREA and pixel_bianchi > pixel_neri:
                print("INCROCIO 180")
                                
                _sendIfChanged(comm.turn180)
            elif pixel_sx > MIN_GREEN_PIXELS_SIDE and area_rettangolo > MIN_GREEN_RECT_AREA and pixel_bianchi > pixel_neri:
                print("INCROCIOsx")
                _sendIfChanged(comm.leftIntersection)
            elif pixel_dx > MIN_GREEN_PIXELS_SIDE and area_rettangolo > MIN_GREEN_RECT_AREA and pixel_bianchi > pixel_neri: 
                print("INCROCIOdx")
                _sendIfChanged(comm.rightIntersection)
            else:
                _lastCommand = None
                comm.drive(centro_sopra[0] - SCREEN_CENTER_X)

            mask_debug = cv2.cvtColor(mask_green, cv2.COLOR_GRAY2BGR)
            cv2.line(mask_debug, (x_c, GREEN_ROI_Y_START), (x_c, GREEN_ROI_Y_END), (255, 0, 0), 2)
            cv2.rectangle(mask_green,
                            (0, GREEN_ROI_Y_START),
                            (max(0, x_c - GREEN_CENTER_OFFSET), GREEN_ROI_Y_END),
                            (0, 255, 0), 2)  # sinistra dinamica (verde)

            cv2.rectangle(mask_green,
                            (min(640, x_c + GREEN_CENTER_OFFSET), GREEN_ROI_Y_START),
                            (640, GREEN_ROI_Y_END),
                            (0, 200, 0), 2)  # destra dinamica (verde scuro)

            # ===== ROI STATICHE =====
            cv2.rectangle(mask_green,
                            (ROI_LEFT_PANEL[0], ROI_LEFT_PANEL[1]),
                            (ROI_LEFT_PANEL[2], ROI_LEFT_PANEL[3]),
                            (255, 0, 255), 2)  # sinistra statica (viola)

            cv2.rectangle(mask_green,
                            (ROI_RIGHT_PANEL[0], ROI_RIGHT_PANEL[1]),
                            (ROI_RIGHT_PANEL[2], ROI_RIGHT_PANEL[3]),
                            (0, 255, 255), 2)  # destra statica (giallo)
                        
            cv2.imshow("verdisicazzo", mask_debug)

    else:
        area_dx = sum(cv2.contourArea(c) for c in filtered_contours_dx)
        area_sx = sum(cv2.contourArea(c) for c in filtered_contours_sx)

        if area_dx > area_sx:
            comm.drive(-SCREEN_CENTER_X)
        elif area_sx > area_dx:
            comm.drive(SCREEN_CENTER_X)

    if len(line.shape) == 2:
        debug_img = cv2.cvtColor(line, cv2.COLOR_GRAY2BGR)
    else:
        debug_img = line.copy()

    cv2.line(debug_img, (SCREEN_CENTER_X, 0), (SCREEN_CENTER_X, 480), (255, 0, 0), 2)

    if centro_sopra[0] != 0:
        cv2.circle(debug_img, (centro_sopra[0], centro_sopra[1]), 8, (0, 255, 0), -1)
        cv2.line(debug_img, (SCREEN_CENTER_X, centro_sopra[1]), (centro_sopra[0], centro_sopra[1]), (0, 255, 255), 2)
        delta = centro_sopra[0] - SCREEN_CENTER_X

        cv2.putText(debug_img, f"delta: {delta}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        direction = "STRAIGHT"
        if delta > 20:
            direction = "RIGHT"
        elif delta < -20:
            direction = "LEFT"

        cv2.putText(debug_img, f"dir: {direction}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(debug_img, f"offset: {centro_sopra[0] - SCREEN_CENTER_X}", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    cv2.imshow("line", debug_img)
    cv2.imshow("copia", copia)
    cv2.imshow("verdisiCAZZO", copia_pulita)
   
   

    return "LINE"