import serial  # type: ignore
import struct

# IMPOSTAZIONI DELLA CONNESSIONE SERIALE

PORT_NAME   = '/dev/ttyUSB0'
BAUD_RATE   = 115200
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

# FUNZIONE DRIVE: INVIA L'OFFSET VISIVO AL FIRMWARE PER IL PID
# FORMATO: 0xFF | 0x03 | HIGH_BYTE | LOW_BYTE  (int16 big-endian, range -32768..32767)

def drive(offset):
    try:
        packed = struct.pack('>h', int(max(-32768, min(32767, offset))))
        serialConn.write(bytes([0xFF, 3]) + packed)
    except Exception as e:
        print(f"Errore drive: {e}")

# FUNZIONE PER RICEVERE I DATI DAI SENSORI (BINARIO)

def getSensors():
    try:
        if serialConn.in_waiting >= 13:
            if serialConn.read(1) == b'\xaa':
                payload = serialConn.read(12)

                # DECODIFICA 1 FLOAT (f) + 4 UINT16 (H) IN LITTLE ENDIAN (<)

                data = struct.unpack('<HHHHf', payload)
                return {
                    "tofFront": data[0],
                    "tofLeft":  data[1],
                    "tofRight": data[2],
                    "tofBack":  data[3],
                    "heading":  data[4]
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

# [INDIETRO]

def backward():
    sendCommand(4)

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
    drive(0)

# CHIUSURA DELLA SERIALE

def release():
    stop()
    serialConn.close()