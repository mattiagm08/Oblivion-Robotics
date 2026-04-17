# config.py

# ─────────────────────────────────────────────
# FINESTRE CV2
# ─────────────────────────────────────────────

WINDOW_NAME_GREEN = "Immagine con sogliatura verde"
WINDOW_NAME_MAIN  = "Main View"
WINDOW_NAME_MASK  = "mask"

# ─────────────────────────────────────────────
# DEBUG
# ─────────────────────────────────────────────

DEBUG_COLOR_RECT = (0, 255, 0)
DEBUG_THICKNESS  = 2

# ─────────────────────────────────────────────
# VERDE HSV — TRACKBAR INITIAL VALUES
# [H_min, S_min, V_min, H_max, S_max, V_max]
# ─────────────────────────────────────────────

GREEN_INITIAL_VALUES = [23, 69, 54, 82, 187, 255]

# ─────────────────────────────────────────────
# SENSORI
# ─────────────────────────────────────────────

TOF_OBSTACLE_DISTANCE = 50      # mm — distanza sotto cui scatta OBSTACLE

# ─────────────────────────────────────────────
# SOGLIE E BLUR — ELABORAZIONE IMMAGINE
# ─────────────────────────────────────────────

THRESHOLD_GRAY_LINE         = 80
THRESHOLD_GRAY_CURVE        = 80
GAUSSIAN_BLUR_KERN          = (11, 11)
GAUSSIAN_BLUR_INTERSECTION  = (15, 15)

# ─────────────────────────────────────────────
# SOGLIE VERDE
# ─────────────────────────────────────────────

MIN_GREEN_RECT_AREA    = 26000  # area minima bounding rect verde per essere considerato
MAX_GREEN_PIXELS_TOTAL = 40000  # sopra questa soglia = due patch verdi (180°)
TURN_180_GREEN_LIMIT   = 40000  # conferma inversione 180° nella ROI ritagliata

# ─────────────────────────────────────────────
# SOGLIE CONTORNI LINEA
# ─────────────────────────────────────────────

MIN_LINE_CONTOUR_AREA = 500     # area minima contorno per non essere rumore
MIN_TOP_LINE_AREA     = 1000    # area minima ROI_TOP_CENTRAL per entrare in logica curva

# ─────────────────────────────────────────────
# STERZO — THRESHOLDS CENTRO X
# ─────────────────────────────────────────────

SCREEN_CENTER_X  = 320
LEFT_THRESHOLD   = 280          # sotto questo → sterza sinistra
RIGHT_THRESHOLD  = 360          # sopra questo  → sterza destra
DELTA_X_LIMIT    = 40           # tolleranza delta tra centro_sotto e centro_gap

# ─────────────────────────────────────────────
# ROI  —  (x_start, y_start, x_end, y_end)
# ─────────────────────────────────────────────

ROI_TOP_CENTRAL = (0,   100, 640, 250)  # zona centrale alta — rilevamento linea principale
ROI_LEFT_PANEL  = (0,    80, 100, 480)  # pannello sinistro  — fallback curva
ROI_RIGHT_PANEL = (540,  80, 640, 480)  # pannello destro    — fallback curva
ROI_BOTTOM      = (0,   380, 640, 480)  # zona bassa         — centro_sotto
ROI_GAP_CHECK   = (0,     0, 640, 100)  # zona alta          — centro_gap