import cv2  # type: ignore
import numpy as np  # type: ignore
import comm

WINDOW_NAME_GREEN = "Immagine con sogliatura verde"
WINDOW_NAME_MAIN  = "Main View"
WINDOW_NAME_MASK  = "mask"
DEBUG_COLOR_RECT  = (0, 255, 0)
DEBUG_THICKNESS   = 2

# VALORI INIZIALI TRACKBAR (HSV)
GREEN_INITIAL_VALUES = [10, 108, 29, 85, 235, 255]

# SOGLIE E PARAMETRI
TOF_OBSTACLE_DISTANCE = 50
THRESHOLD_GRAY_LINE = 80
THRESHOLD_GRAY_CURVE = 90
GAUSSIAN_BLUR_KERN = (11, 11)
GAUSSIAN_BLUR_INTERSECTION = (15, 15)

MIN_GREEN_RECT_AREA = 2000
MAX_GREEN_PIXELS_TOTAL = 120000
MIN_GREEN_PIXELS_SIDE = 2000
MIN_LINE_CONTOUR_AREA = 500
MIN_TOP_LINE_AREA = 1000
TURN_180_GREEN_LIMIT = 120000

SCREEN_CENTER_X = 320
LEFT_THRESHOLD = 280
RIGHT_THRESHOLD = 360
DELTA_X_LIMIT = 40

# ROI E PANNELLI
VV_RIGHT_PANEL   = (600, 100, 800, 500)
VV_LEFT_PANEL    = (0,   100, 200, 500)
ROI_TOP_CENTRAL = (0, 100, 640, 250)
ROI_LEFT_PANEL   = (0,   0, 100, 480)
ROI_RIGHT_PANEL = (540,  0, 640, 480)
ROI_BOTTOM       = (0, 380, 640, 480)
ROI_GAP_CHECK    = (0,   0, 640, 100)

# STATO LOCALE 
_lastCommand = None

# TRACKBAR
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

# SEND IF CHANGED
def _sendIfChanged(cmdFunc):
    global _lastCommand
    if _lastCommand != cmdFunc:
        _lastCommand = cmdFunc
        cmdFunc()

# FUNZIONE INCROCIO
def _incr(img_pulita, img_nocrop):
    curva  = [0, 0]
    copia  = img_pulita.copy()

    copia_verde = cv2.cvtColor(img_nocrop, cv2.COLOR_BGR2HSV)
    copia_verde = cv2.GaussianBlur(copia_verde, GAUSSIAN_BLUR_KERN, cv2.BORDER_REFLECT)

    copia = cv2.cvtColor(copia, cv2.COLOR_BGR2GRAY)
    copia = cv2.GaussianBlur(copia, GAUSSIAN_BLUR_INTERSECTION, cv2.BORDER_REFLECT)
    (_, copia) = cv2.threshold(copia, THRESHOLD_GRAY_LINE, 255, cv2.THRESH_BINARY_INV)

    img_nocrop_hsv = cv2.cvtColor(img_nocrop, cv2.COLOR_BGR2HSV)
    img_nocrop_hsv = cv2.GaussianBlur(img_nocrop_hsv, GAUSSIAN_BLUR_KERN, cv2.BORDER_REFLECT)

    copia_nocrop = cv2.cvtColor(img_nocrop, cv2.COLOR_BGR2GRAY)
    copia_nocrop = cv2.GaussianBlur(copia_nocrop, GAUSSIAN_BLUR_INTERSECTION, cv2.BORDER_REFLECT)
    _, copia_nocrop = cv2.threshold(copia_nocrop, THRESHOLD_GRAY_LINE, 255, cv2.THRESH_BINARY_INV)

    lower_green, upper_green = _getTrackbarValues()
    mask = cv2.inRange(img_nocrop_hsv, lower_green, upper_green)

    VV_LEFT_RECT  = mask[VV_LEFT_PANEL[1]:VV_LEFT_PANEL[3],   VV_LEFT_PANEL[0]:VV_LEFT_PANEL[2]]
    VV_RIGHT_RECT = mask[VV_RIGHT_PANEL[1]:VV_RIGHT_PANEL[3], VV_RIGHT_PANEL[0]:VV_RIGHT_PANEL[2]]
    pixel_vvSx = cv2.countNonZero(VV_LEFT_RECT)
    pixel_vvDx = cv2.countNonZero(VV_RIGHT_RECT)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    mask_debug = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    cv2.rectangle(mask_debug, (VV_LEFT_PANEL[0],  VV_LEFT_PANEL[1]),  (VV_LEFT_PANEL[2],  VV_LEFT_PANEL[3]),  (0, 255, 0), 2)
    cv2.rectangle(mask_debug, (VV_RIGHT_PANEL[0], VV_RIGHT_PANEL[1]), (VV_RIGHT_PANEL[2], VV_RIGHT_PANEL[3]), (0, 255, 0), 2)
    cv2.imshow(WINDOW_NAME_MASK, mask_debug)

    start_cut = (0, 0)
    end_cut   = (0, 0)

    if contours:
        green_contour = max(contours, key=cv2.contourArea)
        M = cv2.moments(green_contour)

        if M["m00"] != 0:
            center_x = int(M["m10"] / M["m00"])
            center_y = int(M["m01"] / M["m00"])
            cv2.circle(copia_verde, (center_x, center_y), 10, (0, 255, 0), -1)

            rect  = cv2.minAreaRect(green_contour)
            box   = cv2.boxPoints(rect)
            box   = np.int8(box)

            scale_x = 640 / 800 * 1.1
            scale_y = 480 / 600 * 0.9

            second_rect_y     = int(rect[0][1] * scale_y) - int(rect[1][1] * scale_y / 2)
            second_rect_x     = int(rect[0][0] * scale_x) - int(rect[1][0] * scale_x / 2)
            second_rect_end_x = int(rect[0][0] * scale_x) + int(rect[1][0] * scale_x / 2)
            second_rect_end_y = int(rect[0][1] * scale_y) + int(rect[1][1] * scale_y / 2)

            cv2.rectangle(copia_verde, (second_rect_x, second_rect_y), (second_rect_end_x, second_rect_end_y), (255, 0, 0), 2)

            area_rettangolo = rect[1][0] * rect[1][1]

            if area_rettangolo > MIN_GREEN_RECT_AREA:
                curva = [0, 0]

                start_point1 = (second_rect_x, second_rect_y - 40)
                end_point1   = (second_rect_end_x, second_rect_y)
                cv2.rectangle(img_pulita, start_point1, end_point1, (255, 0, 0), 2)
                cut_sop = copia_nocrop[start_point1[1]:end_point1[1], start_point1[0]:end_point1[0]]

                bianchi_sop = cv2.countNonZero(cut_sop)
                neri_sop    = cut_sop.size - bianchi_sop

                if bianchi_sop > neri_sop:

                    if pixel_vvSx > MIN_GREEN_PIXELS_SIDE and pixel_vvDx > MIN_GREEN_PIXELS_SIDE:
                        curva = [1, 1]

                    elif pixel_vvSx > MIN_GREEN_PIXELS_SIDE:
                        curva     = [1, 0]
                        start_cut = (0, end_point1[1] - 50)
                        end_cut   = (end_point1[0] + 100, 480)
                        cv2.rectangle(img_pulita, start_cut, end_cut, (0, 255, 0), 2)

                    elif pixel_vvDx > MIN_GREEN_PIXELS_SIDE:
                        curva     = [0, 1]
                        start_cut = (second_rect_x - 100, second_rect_y - 100)
                        end_cut   = (640, 480)
                        cv2.rectangle(img_pulita, start_cut, end_cut, (0, 0, 255), 2)

                    else:
                        curva = [0, 0]

                else:
                    curva = [0, 0]

        cv2.imshow("pulita", img_pulita)

    if (curva[0] == 0 and curva[1] == 0) or (curva[0] == 1 and curva[1] == 1):
        return copia
    elif (curva[0] == 0 and curva[1] == 1) or (curva[0] == 1 and curva[1] == 0):
        img_black = np.zeros_like(copia)
        img_black[start_cut[1]:end_cut[1], start_cut[0]:end_cut[0]] = copia[start_cut[1]:end_cut[1], start_cut[0]:end_cut[0]]
        return img_black

# FUNZIONE CURVA
def _cur(img_pulita, img_nocrop):
    curva      = [0, 0]
    copia      = img_pulita.copy()
    copia_verde = cv2.cvtColor(copia, cv2.COLOR_BGR2HSV)
    copia_verde = cv2.GaussianBlur(copia_verde, GAUSSIAN_BLUR_KERN, cv2.BORDER_REFLECT)

    copia = cv2.cvtColor(copia, cv2.COLOR_BGR2GRAY)
    copia = cv2.GaussianBlur(copia, GAUSSIAN_BLUR_KERN, cv2.BORDER_REFLECT)
    (_, copia) = cv2.threshold(copia, THRESHOLD_GRAY_CURVE, 255, cv2.THRESH_BINARY_INV)

    img_nocrop_hsv = cv2.cvtColor(img_nocrop, cv2.COLOR_BGR2HSV)
    img_nocrop_hsv = cv2.GaussianBlur(img_nocrop_hsv, GAUSSIAN_BLUR_KERN, cv2.BORDER_REFLECT)

    lower_green, upper_green = _getTrackbarValues()
    mask = cv2.inRange(img_nocrop_hsv, lower_green, upper_green)

    VV_LEFT_RECT  = mask[VV_LEFT_PANEL[1]:VV_LEFT_PANEL[3],   VV_LEFT_PANEL[0]:VV_LEFT_PANEL[2]]
    VV_RIGHT_RECT = mask[VV_RIGHT_PANEL[1]:VV_RIGHT_PANEL[3], VV_RIGHT_PANEL[0]:VV_RIGHT_PANEL[2]]
    pixel_vvSx = cv2.countNonZero(VV_LEFT_RECT)
    pixel_vvDx = cv2.countNonZero(VV_RIGHT_RECT)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    mask_debug = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    cv2.rectangle(mask_debug, (VV_LEFT_PANEL[0],  VV_LEFT_PANEL[1]),  (VV_LEFT_PANEL[2],  VV_LEFT_PANEL[3]),  (0, 255, 0), 2)
    cv2.rectangle(mask_debug, (VV_RIGHT_PANEL[0], VV_RIGHT_PANEL[1]), (VV_RIGHT_PANEL[2], VV_RIGHT_PANEL[3]), (0, 255, 0), 2)
    cv2.imshow(WINDOW_NAME_MASK, mask_debug)

    if contours:
        green_contour = max(contours, key=cv2.contourArea)
        M = cv2.moments(green_contour)

        if M["m00"] != 0:
            center_x = int(M["m10"] / M["m00"])
            center_y = int(M["m01"] / M["m00"])
            cv2.circle(copia_verde, (center_x, center_y), 10, (0, 255, 0), -1)

            rect = cv2.minAreaRect(green_contour)
            second_rect_y     = int(rect[0][1]) - int(rect[1][1] / 2)
            second_rect_x     = int(rect[0][0]) - int(rect[1][0] / 2)
            second_rect_end_x = int(rect[0][0]) + int(rect[1][0] / 2)
            second_rect_end_y = int(rect[0][1]) + int(rect[1][1] / 2)

            cv2.rectangle(copia_verde, (second_rect_x, second_rect_y), (second_rect_end_x, second_rect_end_y), (255, 0, 0), 2)

            area_rettangolo = rect[1][0] * rect[1][1]

            if area_rettangolo > MIN_GREEN_RECT_AREA:
                start_point1 = (second_rect_x, second_rect_y - 40)
                end_point1   = (second_rect_end_x, second_rect_y)
                cut_sop      = copia[start_point1[1]:end_point1[1], start_point1[0]:end_point1[0]]

                start_point2 = (second_rect_end_x, second_rect_y)
                end_point2   = (second_rect_end_x + 50, second_rect_end_y)
                cut_latdx    = copia[start_point2[1]:end_point2[1], start_point2[0]:end_point2[0]]

                bianchi_sop = cv2.countNonZero(cut_sop)
                neri_sop    = cut_sop.size - bianchi_sop

                if bianchi_sop > neri_sop:
                    bianchi_latdx = cv2.countNonZero(cut_latdx)
                    neri_latdx    = cut_latdx.size - bianchi_latdx

                    if bianchi_latdx > neri_latdx:
                        if pixel_vvSx > MIN_GREEN_PIXELS_SIDE and pixel_vvDx > MIN_GREEN_PIXELS_SIDE:
                            curva = [1, 1]
                        else:
                            curva = [1, 0]
                    elif bianchi_latdx < neri_latdx:
                        if pixel_vvDx > MIN_GREEN_PIXELS_SIDE and pixel_vvSx > MIN_GREEN_PIXELS_SIDE:
                            curva = [1, 1]
                        else:
                            curva = [0, 1]
                else:
                    curva = [0, 0]

    return curva

# ENTRY POINT
def run(cleanImage):

    # CONTROLLO OSTACOLO ToF
    sensorData = comm.getSensors()
    if sensorData and sensorData['tofFront'] < TOF_OBSTACLE_DISTANCE:
        _sendIfChanged(comm.stop)
        cv2.imshow(WINDOW_NAME_MAIN, cleanImage)
        return "LINE"

    # CROP 640x480 DAL FRAME 800x600
    img_senza_crop = cleanImage.copy()
    copia_pulita   = cleanImage.copy()
    cropX = (800 - 640) // 2
    cropY = (600 - 480) // 2
    copia_pulita = copia_pulita[cropY:cropY + 480, cropX:cropX + 640]

    # CALCOLO MASCHERA
    line = _incr(copia_pulita, img_senza_crop)
    copia = line.copy()

    cv2.imshow(WINDOW_NAME_MAIN, cleanImage)

    # DISEGNO ROI DI DEBUG
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

    # RITAGLIO ROI
    cut_sopra = copia[sp[1]:ep[1], sp[0]:ep[0]]
    cut_dx = copia[sp2[1]:ep2[1], sp2[0]:ep2[0]]
    cut_sx = copia[sp3[1]:ep3[1], sp3[0]:ep3[0]]
    cut_sotto = copia[sp4[1]:ep4[1], sp4[0]:ep4[0]]
    cut_gap = copia[sp5[1]:ep5[1], sp5[0]:ep5[0]]

    # CONTORNI
    contours_sopra, _ = cv2.findContours(cut_sopra, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_dx, _ = cv2.findContours(cut_dx, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_sx, _ = cv2.findContours(cut_sx, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    filtered_contours_sopra = [cnt for cnt in contours_sopra if cv2.contourArea(cnt) > MIN_LINE_CONTOUR_AREA]
    filtered_contours_dx = [cnt for cnt in contours_dx if cv2.contourArea(cnt) > MIN_LINE_CONTOUR_AREA]
    filtered_contours_sx = [cnt for cnt in contours_sx if cv2.contourArea(cnt) > MIN_LINE_CONTOUR_AREA]

    # CENTRI
    M = cv2.moments(cut_sopra)
    Msotto = cv2.moments(cut_sotto)
    Mgap = cv2.moments(cut_gap)

    centro_sopra = [int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]) + ROI_TOP_CENTRAL[1]] if M["m00"] != 0 else [0, 0]
    centro_sotto = [int(Msotto["m10"] / Msotto["m00"]) + ROI_BOTTOM[0], int(Msotto["m01"] / Msotto["m00"])] if Msotto["m00"] != 0 else [0, 0]
    centro_gap = [int(Mgap["m10"] / Mgap["m00"]) + ROI_GAP_CHECK[0], int(Mgap["m01"] / Mgap["m00"])] if Mgap["m00"] != 0 else [0, 0]

    delta_x = centro_sotto[0] - centro_gap[0]
    area_sopra = sum(cv2.contourArea(c) for c in filtered_contours_sopra)

    # LOGICA PRINCIPALE
    if area_sopra > MIN_TOP_LINE_AREA:
        curva = _cur(copia_pulita, img_senza_crop)
        #curva[0] = 0
        #curva[1] = 0

        if curva[0] == 0 and curva[1] == 0:
            # CALCOLO OFFSET VISIVO E INVIO AL PID DEL FIRMWARE
            if centro_sopra[0] == 0:
                _sendIfChanged(comm.stop)
            else:
                _lastCommand = None
                comm.drive(centro_sopra[0] - SCREEN_CENTER_X)

        elif curva[0] == 1 and curva[1] == 0:
            print("INCROCIOsx")
            _sendIfChanged(comm.leftIntersection)

        elif curva[0] == 0 and curva[1] == 1:
            print("INCROCIOdx")
            _sendIfChanged(comm.rightIntersection)

        elif curva[0] == 1 and curva[1] == 1:
            print("INCROCIO 180")
            _sendIfChanged(comm.turn180)

    else:
        area_dx = sum(cv2.contourArea(c) for c in filtered_contours_dx)
        area_sx = sum(cv2.contourArea(c) for c in filtered_contours_sx)

        # RECOVERY
        if area_dx > area_sx:
            comm.drive(-SCREEN_CENTER_X)
        elif area_sx > area_dx:
            comm.drive(SCREEN_CENTER_X)

    # SHOW DEBUG
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
        if delta > 20: direction = "RIGHT"
        elif delta < -20: direction = "LEFT"

        cv2.putText(debug_img, f"dir: {direction}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(debug_img, f"offset: {centro_sopra[0] - SCREEN_CENTER_X}", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    cv2.imshow("line", debug_img)
    cv2.imshow("copia", copia)

    return "LINE"