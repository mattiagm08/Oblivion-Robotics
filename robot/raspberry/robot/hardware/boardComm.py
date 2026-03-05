import serial
import threading
import time
from config import SERIAL_PORT, BAUD_RATE

class BoardComm:
    """
    ###########################################################################
    # SERIALE ESP32 - COMUNICAZIONE                                           #
    ###########################################################################
    # PROTOCOLLO INVIO (Raspberry -> ESP32):                                  #
    #   <OFF:0.35,SPD:150>                                                    #
    #                                                                         #
    # PROTOCOLLO RICEZIONE (ESP32 -> Raspberry):                              #
    #   <TF:123,TS:80,TD:90,HEAD:45.2,ENL:500,ENR:498>                        #
    #   TF  = ToF frontale  (mm)                                              #
    #   TS  = ToF sinistra  (mm)                                              #
    #   TD  = ToF destra    (mm)                                              #
    #   HEAD = heading IMU   (gradi)                                          #
    #   ENL = encoder sx    (ricevuto, non utilizzato dalla FSM)              #
    #   ENR = encoder dx    (ricevuto, non utilizzato dalla FSM)              #
    ###########################################################################
    """

    def __init__(self):

        # APERTURA PORTA SERIALE
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
            self.ser.flush()
        except Exception as e:
            print(f"[ERROR] Impossibile aprire la porta seriale: {e}")
            self.ser = None

        # VARIABILI SENSORI
        self.distanceFront = 9999.0
        self.distanceLeft  = 9999.0
        self.distanceRight = 9999.0
        self.heading       = 0.0
        self._encL         = 0   
        self._encR         = 0   

        # THREAD DI LETTURA CONTINUA
        self.running = True
        self.thread  = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    def _read_loop(self):
        # PROTOCOLLO RICEZIONE: <TF:VAL,TS:VAL,TD:VAL,HEAD:VAL,ENL:VAL,ENR:VAL>
        while self.running and self.ser:
            if self.ser.in_waiting > 0:
                try:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if not line:
                        continue

                    if line.startswith("<") and line.endswith(">"):
                        line = line[1:-1]

                    for p in line.split(','):
                        if ":" not in p:
                            continue
                        key, value = p.split(":", 1)
                        key = key.strip()

                        if   key == "TF":   self.distanceFront = float(value)
                        elif key == "TS":   self.distanceLeft  = float(value)
                        elif key == "TD":   self.distanceRight = float(value)
                        elif key == "HEAD": self.heading       = float(value)
                        elif key == "ENL":  self._encL         = int(value)
                        elif key == "ENR":  self._encR         = int(value)

                except (ValueError, IndexError):
                    pass
                except Exception as e:
                    print(f"[SERIAL DEBUG] Errore lettura: {e}")

            time.sleep(0.01)

    def sendControl(self, offset, speed):
        # PROTOCOLLO INVIO: <OFF:0.35,SPD:150>
        if self.ser:
            msg = f"<OFF:{round(offset, 2)},SPD:{int(speed)}>\n"
            try:
                self.ser.write(msg.encode('utf-8'))
            except Exception:
                pass

    def getDistanceFront(self):
        return self.distanceFront

    def getDistanceLeft(self):
        return self.distanceLeft

    def getDistanceRight(self):
        return self.distanceRight

    def getDistance(self):
        return self.distanceFront

    def getHeading(self):
        return self.heading

    def close(self):
        self.running = False
        if self.ser:
            self.ser.close()