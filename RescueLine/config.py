import cv2 # type: ignore

# Variabili globali e parametri di controllo
k_p = 10  # Increased Proportional control gain
vel_dx = 80
vel_sx = 80
cor = 15
vel = 94

# Configurazione Trackbar e Finestre
window_name = "Immagine con sogliatura verde"
initial_values = [23, 69, 54, 82, 187, 255]

def init_trackbars():
    cv2.namedWindow(window_name)
    cv2.createTrackbar("H_min", window_name, initial_values[0], 179, lambda x: None)
    cv2.createTrackbar("S_min", window_name, initial_values[1], 255, lambda x: None)
    cv2.createTrackbar("V_min", window_name, initial_values[2], 255, lambda x: None)
    cv2.createTrackbar("H_max", window_name, initial_values[3], 179, lambda x: None)
    cv2.createTrackbar("S_max", window_name, initial_values[4], 255, lambda x: None)
    cv2.createTrackbar("V_max", window_name, initial_values[5], 255, lambda x: None)