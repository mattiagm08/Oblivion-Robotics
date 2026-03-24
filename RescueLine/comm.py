import serial # type: ignore

ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)

def invia_comando(comando):
    """Funzione di supporto per inviare i dati via seriale"""
    try:
        ser.write((comando + '\n').encode('utf-8'))
    except Exception as e:
        print(f"Errore seriale: {e}")

def general_begin():
    # Sistema tutti i servo o invia segnale di avvio
    invia_comando("START")

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

def rilascia():
    # Invia stop e chiudi seriale
    stop()
    ser.close()