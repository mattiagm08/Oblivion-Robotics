import serial # type: ignore
import struct

# IMPOSTAZIONI DELLA CONNESSIONE SERIALE

PORT_NAME = '/dev/ttyUSB0'
BAUD_RATE = 115200
TIMEOUT_VAL = 0.1

# INIZIALIZZAZIONE DELL'OGGETTO SERIALE

serialConn = serial.Serial(PORT_NAME, BAUD_RATE, timeout = TIMEOUT_VAL)

# FUNZIONE PER INVIARE I DATI VIA SERIALE

def sendCommand(command):
    try:
        # INVIO DI UN HEADER (0xFF) SEGUITO DAL COMANDO PER SINCRONIZZAZIONE

        serialConn.write(bytes([0xFF, command]))
    except Exception as e:
        print(f"Errore seriale: {e}")

# FUNZIONE PER RICEVERE I DATI DAI SENSORI (BINARIO)

def getSensors():
    try:
        if serialConn.in_waiting >= 11:
            if serialConn.read(1) == b'\xaa':
                payload = serialConn.read(10)

                # DECODIFICA 1 FLOAT (f) + 3 UINT16 (H) IN LITTLE ENDIAN (<)

                data = struct.unpack('<HHHf', payload)
                return {
                    "tofFront": data[0],
                    "tofLeft": data[1],
                    "tofRight": data[2],
                    "heading": data[3]
                }
                
    except Exception as e:
        print(f"Errore ricezione: {e}")
    return None

# AVVIO E STOP COMANDI SERIALE

def begin():
    sendCommand(1)

def stop():
    sendCommand(2)

# FUNZIONI DI MOVIMENTO TRAMITE SERIALE

# [AVANTI]

def forward():
    sendCommand(3)

# [INDIETRO]

def backward():
    sendCommand(4)

# [SINISTRA]

def left():
    sendCommand(5)

# [DESTRA]

def right():
    sendCommand(6)

# [INCROCIO SINISTRO]
    
def leftIntersection():
    sendCommand(7)

# [INCROCIO DESTRO]
    
def rightIntersection():
    sendCommand(8)

# [INVERSIONE]

def turn180():
    sendCommand(9)

# [ARGENTO]

def isSilver():
    sendCommand(10)

# [FINE]

def isRed():
    sendCommand(11)

# [DEFAULT]

def default():
    sendCommand(3)

# CHIUSURA DELLA SERIALE

def release():
    stop()
    serialConn.close()