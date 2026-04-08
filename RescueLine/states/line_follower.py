# LIBRERIE IMPORTATE

import cv2 # type: ignore
import numpy as np # type: ignore
import config
import comm

# CONFIGURAZIONE DELLE FINESTRE E VALORI INIZIALI

def initTrackbars():

    # INIZIALIZZAZIONE DELLA FINESTRA DEI TRACKBAR PER IL FILTRAGGIO COLORE
    
    cv2.namedWindow(config.WINDOW_NAME_GREEN)
    
    # CREAZIONE DEI TRACKBAR PER IL RANGE HSV (MIN E MAX)

    cv2.createTrackbar("H_min", config.WINDOW_NAME_GREEN, config.GREEN_INITIAL_VALUES[0], 179, lambda x: None)
    cv2.createTrackbar("S_min", config.WINDOW_NAME_GREEN, config.GREEN_INITIAL_VALUES[1], 255, lambda x: None)
    cv2.createTrackbar("V_min", config.WINDOW_NAME_GREEN, config.GREEN_INITIAL_VALUES[2], 255, lambda x: None)
    cv2.createTrackbar("H_max", config.WINDOW_NAME_GREEN, config.GREEN_INITIAL_VALUES[3], 179, lambda x: None)
    cv2.createTrackbar("S_max", config.WINDOW_NAME_GREEN, config.GREEN_INITIAL_VALUES[4], 255, lambda x: None)
    cv2.createTrackbar("V_max", config.WINDOW_NAME_GREEN, config.GREEN_INITIAL_VALUES[5], 255, lambda x: None)

# FUNZIONE VUOTA PER IL TRACKBAR

def onTrackbarChange(value):
    pass

# FUNZIONE PER RILEVARE L'INCROCIO

def intersection(cleanImage):

    # INIZIALIZZAZIONE DELLA CURVA E PREPARAZIONE IMMAGINE

    curve = [0, 0]
    copyImg = cleanImage.copy()
    greenCopy = cv2.cvtColor(copyImg, cv2.COLOR_BGR2HSV)
    greenCopy = cv2.GaussianBlur(greenCopy, config.GAUSSIAN_BLUR_KERN, cv2.BORDER_REFLECT)
    copyImg = cv2.cvtColor(copyImg, cv2.COLOR_BGR2GRAY)
    copyImg = cv2.GaussianBlur(copyImg, config.GAUSSIAN_BLUR_INTERSECTION, cv2.BORDER_REFLECT)
    (_, copyImg) = cv2.threshold(copyImg, config.THRESHOLD_GRAY_LINE, 255, cv2.THRESH_BINARY_INV)

    # RITAGLIO DELL'IMMAGINE PER LA RICERCA DELL'INCROCIO

    startPoint5 = (0, 0)
    endPoint5 = (640, 480)
    cutIntersection = greenCopy[startPoint5[1]:endPoint5[1], startPoint5[0]:endPoint5[0]]
    
    # LETTURA DEI VALORI DAL TRACKBAR

    hMin = cv2.getTrackbarPos("H_min", config.WINDOW_NAME_GREEN)
    sMin = cv2.getTrackbarPos("S_min", config.WINDOW_NAME_GREEN)
    vMin = cv2.getTrackbarPos("V_min", config.WINDOW_NAME_GREEN)
    hMax = cv2.getTrackbarPos("H_max", config.WINDOW_NAME_GREEN)
    sMax = cv2.getTrackbarPos("S_max", config.WINDOW_NAME_GREEN)
    vMax = cv2.getTrackbarPos("V_max", config.WINDOW_NAME_GREEN)

    # CREAZIONE DELLE MASCHERE PER IL COLORE VERDE

    lowerGreen = np.array([hMin, sMin, vMin])
    upperGreen = np.array([hMax, sMax, vMax])

    mask = cv2.inRange(cutIntersection, lowerGreen, upperGreen)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    greenPixels = cv2.countNonZero(mask)
    cv2.imshow(config.WINDOW_NAME_MASK, mask)
    
    # INIZIALIZZAZIONE VARIABILI DI TAGLIO PER EVITARE ERRORI

    startCut = (0, 0)
    endCut = (0, 0)

    # RICERCA DEI CONTORNI VERDI

    if contours:
        greenContour = max(contours, key = cv2.contourArea)
        moments = cv2.moments(greenContour)
        
        if moments["m00"] != 0:

            # CALCOLO DEL CENTRO DEL CONTORNO

            centerX = int(moments["m10"] / moments["m00"])
            centerY = int(moments["m01"] / moments["m00"])
            centerY = centerY + 0
            cv2.circle(greenCopy, (centerX, centerY), 10, (0, 255, 0), -1)
            
            # CREAZIONE DEL RETTANGOLO SUL CONTORNO

            rect = cv2.minAreaRect(greenContour)
            box = cv2.boxPoints(rect)
            box = np.int8(box)

            # CALCOLO DELLE COORDINATE DEL SECONDO RETTANGOLO

            secondRectY = int(rect[0][1]) - int(rect[1][1] / 2)
            secondRectX = int(rect[0][0]) - int(rect[1][0] / 2)
            secondRectEndX = int(rect[0][0]) + int(rect[1][0] / 2)
            secondRectEndY = int(rect[0][1]) + int(rect[1][1] / 2)
            
            cv2.rectangle(greenCopy, (secondRectX, secondRectY), (secondRectEndX, secondRectEndY), (255, 0, 0), 2)

            rectArea = rect[1][0] * rect[1][1]
            
            # CONTROLLO DELL'AREA DEL RETTANGOLO E DEI PIXEL VERDI

            if rectArea > config.MIN_GREEN_RECT_AREA and greenPixels < config.MAX_GREEN_PIXELS_TOTAL:
                curve = [0, 0]
                startPoint1 = (secondRectX, secondRectY - 40)
                endPoint1 = (secondRectEndX, secondRectY)
                cv2.rectangle(cleanImage, startPoint1, endPoint1, (255, 0, 0), 2)
                cutTop = copyImg[startPoint1[1]:endPoint1[1], startPoint1[0]:endPoint1[0]]
                
                startPoint2 = (secondRectEndX, secondRectY)
                endPoint2 = (secondRectEndX + 50, secondRectEndY)
                cv2.rectangle(cleanImage, startPoint2, endPoint2, (255, 0, 0), 2)
                cutRightSide = copyImg[startPoint2[1]:endPoint2[1], startPoint2[0]:endPoint2[0]]
                
                # CONTEGGIO DEI PIXEL BIANCHI E NERI NELLA PARTE SUPERIORE

                whiteTop = cv2.countNonZero(cutTop)
                blackTop = cutTop.size - whiteTop
                
                if whiteTop > blackTop:

                    # CONTEGGIO DEI PIXEL BIANCHI E NERI NELLA PARTE LATERALE DESTRA

                    whiteRightSide = cv2.countNonZero(cutRightSide)
                    blackRightSide = cutRightSide.size - whiteRightSide
                    
                    if whiteRightSide > blackRightSide:
                        curve = [1, 0]
                        startCut = (0, endPoint1[1] - 50)
                        endCut = (endPoint1[0] + 100, 480)
                        cv2.rectangle(cleanImage, startCut, endCut, (0, 255, 0), 2)
                    elif whiteRightSide < blackRightSide:
                        curve = [0, 1]
                        startCut = (secondRectX - 100, secondRectY - 100)
                        endCut = (640, 480)
                        cv2.rectangle(cleanImage, startCut, endCut, (0, 0, 255), 2)
                else:
                    curve = [0, 0]
            elif greenPixels > config.MAX_GREEN_PIXELS_TOTAL:
                curve = [1, 1]
                
        cv2.imshow("pulita", cleanImage)
        
    # RESTITUZIONE DELL'IMMAGINE MASCHERATA A SECONDA DELLA CURVA

    if (curve[0] == 0 and curve[1] == 0) or (curve[0] == 1 and curve[1] == 1):
        return copyImg
    elif (curve[0] == 0 and curve[1] == 1) or (curve[0] == 1 and curve[1] == 0):
        blackImg = np.zeros_like(copyImg)
        blackImg[startCut[1]:endCut[1], startCut[0]:endCut[0]] = copyImg[startCut[1]:endCut[1], startCut[0]:endCut[0]]
        return blackImg

# FUNZIONE PER GESTIRE LA CURVA (MOLTO SIMILE A INTERSECTION)

def getCurve(cleanImage):

    # INIZIALIZZAZIONE DELLA CURVA E PREPARAZIONE IMMAGINE

    curve = [0, 0]
    copyImg = cleanImage.copy()
    greenCopy = cv2.cvtColor(copyImg, cv2.COLOR_BGR2HSV)
    greenCopy = cv2.GaussianBlur(greenCopy, config.GAUSSIAN_BLUR_KERN, cv2.BORDER_REFLECT)
    copyImg = cv2.cvtColor(copyImg, cv2.COLOR_BGR2GRAY)
    copyImg = cv2.GaussianBlur(copyImg, config.GAUSSIAN_BLUR_KERN, cv2.BORDER_REFLECT)
    (_, copyImg) = cv2.threshold(copyImg, config.THRESHOLD_GRAY_CURVE, 255, cv2.THRESH_BINARY_INV)
    
    # RITAGLIO DELL'IMMAGINE

    startPoint5 = (0, 0)
    endPoint5 = (640, 480)
    cutIntersection = greenCopy[startPoint5[1]:endPoint5[1], startPoint5[0]:endPoint5[0]]
    
    # LETTURA DEI VALORI DAL TRACKBAR

    hMin = cv2.getTrackbarPos("H_min", config.WINDOW_NAME_GREEN)
    sMin = cv2.getTrackbarPos("S_min", config.WINDOW_NAME_GREEN)
    vMin = cv2.getTrackbarPos("V_min", config.WINDOW_NAME_GREEN)
    hMax = cv2.getTrackbarPos("H_max", config.WINDOW_NAME_GREEN)
    sMax = cv2.getTrackbarPos("S_max", config.WINDOW_NAME_GREEN)
    vMax = cv2.getTrackbarPos("V_max", config.WINDOW_NAME_GREEN)

    # CREAZIONE DELLE MASCHERE PER IL COLORE VERDE

    lowerGreen = np.array([hMin, sMin, vMin])
    upperGreen = np.array([hMax, sMax, vMax])

    mask = cv2.inRange(cutIntersection, lowerGreen, upperGreen)
    greenPixels = cv2.countNonZero(mask)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # RICERCA DEI CONTORNI VERDI E CALCOLO DELLA CURVA

    if contours:
        greenContour = max(contours, key=cv2.contourArea)
        moments = cv2.moments(greenContour)
        
        if moments["m00"] != 0:
            centerX = int(moments["m10"] / moments["m00"])
            centerY = int(moments["m01"] / moments["m00"])
            cv2.circle(greenCopy, (centerX, centerY), 10, (0, 255, 0), -1)
            
            rect = cv2.minAreaRect(greenContour)
            secondRectY = int(rect[0][1]) - int(rect[1][1] / 2)
            secondRectX = int(rect[0][0]) - int(rect[1][0] / 2)
            secondRectEndX = int(rect[0][0]) + int(rect[1][0] / 2)
            secondRectEndY = int(rect[0][1]) + int(rect[1][1] / 2)
            
            cv2.rectangle(greenCopy, (secondRectX, secondRectY), (secondRectEndX, secondRectEndY), (255, 0, 0), 2)

            rectArea = rect[1][0] * rect[1][1]
            if rectArea > config.MIN_GREEN_RECT_AREA:
                startPoint1 = (secondRectX, secondRectY - 40)
                endPoint1 = (secondRectEndX, secondRectY)
                cutTop = copyImg[startPoint1[1]:endPoint1[1], startPoint1[0]:endPoint1[0]]
                
                startPoint2 = (secondRectEndX, secondRectY)
                endPoint2 = (secondRectEndX + 50, secondRectEndY)
                cutRightSide = copyImg[startPoint2[1]:endPoint2[1], startPoint2[0]:endPoint2[0]]
                
                whiteTop = cv2.countNonZero(cutTop)
                blackTop = cutTop.size - whiteTop
                
                if whiteTop > blackTop:
                    whiteRightSide = cv2.countNonZero(cutRightSide)
                    blackRightSide = cutRightSide.size - whiteRightSide
                    
                    if whiteRightSide > blackRightSide:
                        if greenPixels < config.MAX_GREEN_PIXELS_TOTAL:
                            curve = [1, 0]
                        elif greenPixels > config.MAX_GREEN_PIXELS_TOTAL:
                            startCut2 = (0, secondRectY - 40)
                            endCut2 = (640, 480)
                            cut180 = mask[startCut2[1]:endCut2[1], startCut2[0]:endCut2[0]]
                            greenPixels = cv2.countNonZero(cut180)
                            if greenPixels > config.TURN_180_GREEN_LIMIT:
                                curve = [1, 1]
                            else:
                                curve = [1, 0]
                    elif whiteRightSide < blackRightSide:
                        if greenPixels < config.MAX_GREEN_PIXELS_TOTAL:
                            curve = [0, 1]
                        elif greenPixels > config.MAX_GREEN_PIXELS_TOTAL:
                            startCut2 = (0, secondRectY - 40)
                            endCut2 = (640, 480)
                            cut180 = mask[startCut2[1]:endCut2[1], startCut2[0]:endCut2[0]]
                            greenPixels = cv2.countNonZero(cut180)
                            if greenPixels > config.TURN_180_GREEN_LIMIT:
                                curve = [1, 1]
                            else:
                                curve = [0, 1]
                else:
                    curve = [0, 0]
    return curve

# FUNZIONE DI VALIDAZIONE

def validate(frame):
    return 0

# LOOP PRINCIPALE DEL FOLLOWER

def run(cleanImage):

    # RICEZIONE DATI SENSORI DALLA SERIALE (HEADER 0xAA + 10 BYTE)
    
    sensorData = comm.getSensors()

    # OBSTACLE AVOIDING

    #if sensorData and sensorData['tofFront'] < config.TOF_OBSTACLE_DISTANCE:
    #    comm.stop()
    #    return "OBSTACLE"

    # INIZIALIZZAZIONE IMMAGINI E CHIAMATA INTERSECTION

    cleanCopy = cleanImage.copy()
    lineImg = intersection(cleanImage)
    copyImg = lineImg.copy()
    
    cv2.imshow("Test", cleanImage)
    
    # COORDINATE DELLE AREE DI INTERESSE

    startPoint = (config.ROI_TOP_CENTRAL[0], config.ROI_TOP_CENTRAL[1]); endPoint = (config.ROI_TOP_CENTRAL[2], config.ROI_TOP_CENTRAL[3])
    startPoint2 = (config.ROI_LEFT_PANEL[0], config.ROI_LEFT_PANEL[1]); endPoint2 = (config.ROI_LEFT_PANEL[2], config.ROI_LEFT_PANEL[3])
    startPoint3 = (config.ROI_RIGHT_PANEL[0], config.ROI_RIGHT_PANEL[1]); endPoint3 = (config.ROI_RIGHT_PANEL[2], config.ROI_RIGHT_PANEL[3])
    startPoint4 = (config.ROI_BOTTOM[0], config.ROI_BOTTOM[1]); endPoint4 = (config.ROI_BOTTOM[2], config.ROI_BOTTOM[3])
    startPoint5 = (config.ROI_GAP_CHECK[0], config.ROI_GAP_CHECK[1]); endPoint5 = (config.ROI_GAP_CHECK[2], config.ROI_GAP_CHECK[3])
    
    # COSTANTI PER IL DISEGNO DEI RETTANGOLI

    COLOR = config.DEBUG_COLOR_RECT
    THICKNESS = config.DEBUG_THICKNESS
    
    # DISEGNO DELLE AREE DI INTERESSE

    cv2.rectangle(copyImg, startPoint, endPoint, COLOR, THICKNESS)
    cv2.rectangle(copyImg, startPoint2, endPoint2, COLOR, THICKNESS)
    cv2.rectangle(copyImg, startPoint3, endPoint3, COLOR, THICKNESS)
    cv2.rectangle(copyImg, startPoint4, endPoint4, COLOR, THICKNESS)
    cv2.rectangle(copyImg, startPoint5, endPoint5, COLOR, THICKNESS)
    
    # RITAGLIO DELLE AREE DI INTERESSE

    cutTop = copyImg[startPoint[1]:endPoint[1], startPoint[0]:endPoint[0]]
    cutLeft = copyImg[startPoint2[1]:endPoint2[1], startPoint2[0]:endPoint2[0]]
    cutRight = copyImg[startPoint3[1]:endPoint3[1], startPoint3[0]:endPoint3[0]]
    cutBottom = copyImg[startPoint4[1]:endPoint4[1], startPoint4[0]:endPoint4[0]]
    cutGap = copyImg[startPoint5[1]:endPoint5[1], startPoint5[0]:endPoint5[0]]
    
    # RICERCA DEI CONTORNI NELLE VARIE AREE

    contoursTop, _ = cv2.findContours(cutTop, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contoursLeft, _ = cv2.findContours(cutLeft, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contoursRight, _ = cv2.findContours(cutRight, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contoursBottom, _ = cv2.findContours(cutBottom, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contoursGap, _ = cv2.findContours(cutGap, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # FILTRAGGIO DEI CONTORNI IN BASE ALL'AREA MINIMA

    MIN_AREA = config.MIN_LINE_CONTOUR_AREA
    filteredContoursTop = [cnt for cnt in contoursTop if cv2.contourArea(cnt) > MIN_AREA]
    filteredContoursLeft = [cnt for cnt in contoursLeft if cv2.contourArea(cnt) > MIN_AREA]
    filteredContoursRight = [cnt for cnt in contoursRight if cv2.contourArea(cnt) > MIN_AREA]
    
    # CALCOLO DEI MOMENTI PER I CENTRI DI MASSA

    momentsTop = cv2.moments(cutTop)
    momentsBottom = cv2.moments(cutBottom)
    momentsGap = cv2.moments(cutGap)
    
    # CALCOLO DEI CENTRI

    centerTop = [int(momentsTop["m10"]/momentsTop["m00"]), int(momentsTop["m01"]/momentsTop["m00"]) + config.ROI_TOP_CENTRAL[1]] if momentsTop["m00"] != 0 else [0,0]
    centerBottom = [int(momentsBottom["m10"]/momentsBottom["m00"]) + config.ROI_BOTTOM[0], int(momentsBottom["m01"]/momentsBottom["m00"])] if momentsBottom["m00"] != 0 else [0,0]
    centerGap = [int(momentsGap["m10"]/momentsGap["m00"]) + config.ROI_GAP_CHECK[0], int(momentsGap["m01"]/momentsGap["m00"])] if momentsGap["m00"] != 0 else [0,0]
    
    # CALCOLO DELLE DIFFERENZE E DELLE AREE

    deltaX = centerBottom[0] - centerGap[0]
    areaTop = sum(cv2.contourArea(c) for c in filteredContoursTop)
    
    # LOGICA DI MOVIMENTO

    if areaTop > config.MIN_TOP_LINE_AREA:
        curve = getCurve(cleanCopy)
        
        # [AVANTI O CORREZIONE]

        if curve[0] == 0 and curve[1] == 0:
            if (config.LEFT_THRESHOLD <= centerTop[0] <= config.RIGHT_THRESHOLD) or (-config.DELTA_X_LIMIT < deltaX < config.DELTA_X_LIMIT):
                comm.forward()
            elif centerTop[0] < config.LEFT_THRESHOLD:
                comm.left()
            elif centerTop[0] > config.RIGHT_THRESHOLD:
                comm.right()
                
        # [INCROCIO SINISTRO]

        elif curve[0] == 1 and curve[1] == 0:
            comm.leftIntersection()
            print("INTERSECTION LEFT")
            
        # [INCROCIO DESTRO]

        elif curve[0] == 0 and curve[1] == 1:
            comm.rightIntersection()
            print("INTERSECTION RIGHT")
            
        # [INVERSIONE]

        elif curve[0] == 1 and curve[1] == 1:
            comm.turn180()
            print("INTERSECTION 180")
    else:

        # LOGICA PER QUANDO MANCA LA LINEA SUPERIORE

        areaLeft = sum(cv2.contourArea(c) for c in filteredContoursLeft)
        areaRight = sum(cv2.contourArea(c) for c in filteredContoursRight)
        if areaRight > areaLeft: 
            comm.left()
        elif areaLeft > areaRight: 
            comm.right()

    cv2.imshow("line", lineImg)
    cv2.imshow("Clean Image", cleanImage)
    
    # RITORNA LO STATO CORRENTE

    return "LINE"