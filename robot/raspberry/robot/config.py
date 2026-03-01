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

MAX_SPEED = 180   # VELOCITÀ MASSIMA UTILIZZATA NEI TRATTI RETTILINEI
MIN_SPEED = 110   # VELOCITÀ MINIMA PER CURVE STRETTE O CORREZIONI AGGRESSIVE
GAP_SPEED = 130   # VELOCITÀ COSTANTE DURANTE ATTRAVERSAMENTO GAP


# ##########################################################################
# PARAMETRI DI VISIONE - RANGE COLORE IN SPAZIO HSV                        #
# ##########################################################################

# RANGE HSV PER RILEVAMENTO LINEA NERA
LOWER_BLACK = [0, 0, 0]        # SOGLIA INFERIORE COLORE NERO
UPPER_BLACK = [180, 255, 75]   # SOGLIA SUPERIORE COLORE NERO

# RANGE HSV PER RILEVAMENTO MARCATORI VERDI (INCROCI)
LOWER_GREEN = [45, 50, 50]     # SOGLIA INFERIORE COLORE VERDE
UPPER_GREEN = [85, 255, 255]   # SOGLIA SUPERIORE COLORE VERDE

# RANGE HSV PER RILEVAMENTO NASTRO ARGENTO (EVACUATION ZONE)
LOWER_SILVER = [0, 0, 160]     # SOGLIA INFERIORE ARGENTO (ALTA LUMINOSITÀ, BASSA SATURAZIONE)
UPPER_SILVER = [180, 50, 255]  # SOGLIA SUPERIORE ARGENTO


# ##########################################################################
# SOGLIE FISICHE E TEMPORALI                                               #
# ##########################################################################

OBSTACLE_DISTANCE = 150  # DISTANZA MINIMA OSTACOLO IN MILLIMETRI (SOTTO QUESTA SOGLIA SI ATTIVA EVITAMENTO)
GAP_TIMEOUT = 2.5        # TEMPO MASSIMO IN SECONDI SENZA LINEA PRIMA DI DICHIARARE FALLIMENTO GAP


# ##########################################################################
# ROI (REGION OF INTEREST) - DEFINIZIONE ZONE ANALISI FRAME                #
# ##########################################################################
# LE PERCENTUALI SONO RELATIVE ALL'ALTEZZA TOTALE DEL FRAME DELLA CAMERA   #
# ROI BASSA: CONTROLLO STERZO IMMEDIATO                                    #
# ROI ALTA: REGOLAZIONE VELOCITÀ E PREVISIONE TRAIETTORIA                  #
# ##########################################################################

ROI_LOW_Y = 0.70   # POSIZIONE VERTICALE DI INIZIO ROI BASSA
ROI_LOW_H = 0.20   # ALTEZZA ROI BASSA

ROI_HIGH_Y = 0.35  # POSIZIONE VERTICALE DI INIZIO ROI ALTA
ROI_HIGH_H = 0.15  # ALTEZZA ROI ALTA