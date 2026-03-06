"""
###########################################################################
# PARAMETRI GLOBALI DEL ROBOT - CONFIGURAZIONE                            #
###########################################################################
# Definisce costanti operative utilizzate dalla FSM, sensori e controllo  #
# Motori. Modificare qui per ottimizzazione e taratura sistema.           #
###########################################################################
"""

# ##########################################################################
# COMUNICAZIONE SERIALE CON MICROCONTROLLORE (ESP32)                       #
# ##########################################################################

SERIAL_PORT = "/dev/ttyUSB0"  # PORTA SERIALE UTILIZZATA PER LA COMUNICAZIONE
BAUD_RATE = 115200            # VELOCITÀ DI TRASMISSIONE DATI (BIT AL SECONDO)

# ##########################################################################
# PARAMETRI VELOCITÀ MOTORI (SCALA 0-255)                                  #
# ##########################################################################

MAX_SPEED = 200   # VELOCITÀ MASSIMA UTILIZZATA NEI TRATTI RETTILINEI
MIN_SPEED = 120   # VELOCITÀ MINIMA PER CURVE STRETTE O CORREZIONI AGGRESSIVE
GAP_SPEED = 100   # VELOCITÀ COSTANTE DURANTE ATTRAVERSAMENTO GAP
BACK_SPEED = 180  # VELOCITÀ IN RETROMARCIA DURANTE FASE DI RECUPERO DOPO PERDITA LINEA PROLUNGATA

# ##########################################################################
# PARAMETRI DI VISIONE - RANGE COLORE IN SPAZIO HSV                        #
# ##########################################################################

# RANGE HSV PER RILEVAMENTO LINEA NERA
LOWER_BLACK = [0,   0,   0]
UPPER_BLACK = [180, 255, 110]

# RANGE HSV PER RILEVAMENTO MARCATORI VERDI (INCROCI)
LOWER_GREEN = [45, 50,  50]
UPPER_GREEN = [85, 255, 255]

# RANGE HSV PER NASTRO ARGENTO RIFLETTENTE (INGRESSO EVACUATION ZONE)
LOWER_SILVER = [0,   0,  220]
UPPER_SILVER = [180, 40, 255]

# RANGE HSV PER NASTRO ROSSO (GOAL TILE - FINE PERCORSO)
LOWER_RED1 = [0,   120, 80]
UPPER_RED1 = [10,  255, 255]
LOWER_RED2 = [170, 120, 80]
UPPER_RED2 = [180, 255, 255]

# ##########################################################################
# SOGLIE FISICHE E TEMPORALI                                               #
# ##########################################################################

OBSTACLE_DISTANCE = 150  # DISTANZA MINIMA OSTACOLO IN mm
GAP_TIMEOUT       = 1.75  # TIMEOUT GAP IN SECONDI

# ##########################################################################
# ROI (REGION OF INTEREST) - DEFINIZIONE ZONE ANALISI FRAME                #
# ##########################################################################
# LE PERCENTUALI SONO RELATIVE ALL'ALTEZZA TOTALE DEL FRAME DELLA CAMERA   #
# ROI BASSA: CONTROLLO STERZO IMMEDIATO                                    #
# ROI ALTA:  REGOLAZIONE VELOCITÀ E PREVISIONE TRAIETTORIA                 #
# ##########################################################################

ROI_LOW_Y = 0.70   # POSIZIONE VERTICALE DI INIZIO ROI BASSA
ROI_LOW_H = 0.20   # ALTEZZA ROI BASSA

ROI_HIGH_Y = 0.35  # POSIZIONE VERTICALE DI INIZIO ROI ALTA
ROI_HIGH_H = 0.15  # ALTEZZA ROI ALTA