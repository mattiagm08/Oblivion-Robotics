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
    #   <OFF:0.35,SPD:150,SH:0>                                               #
    #   OFF = offset sterzo  (-1.0 … +1.0)                                   #
    #   SPD = velocità base  (int, negativo = retromarcia)                    #
    #   SH  = shake attivo   (0 = no, 1 = sì)                                #
    #                                                                         #
    # PROTOCOLLO RICEZIONE (ESP32 -> Raspberry):                              #
    #   <TF:123,TS:80,TD:90,HEAD:45.2,ENL:500,ENR:498>                        #
    #   TF   = ToF frontale  (mm)                                             #
    #   TS   = ToF sinistra  (mm)                                             #
    #   TD   = ToF destra    (mm)                                             #
    #   HEAD = heading IMU   (gradi)                                          #
    #   ENL  = encoder sx                                                     #
    #   ENR  = encoder dx                                                     #
    ###########################################################################
    """

    #<OFF:VAL,SPD:VAL,SH:VAL>
    #<TF:VAL,TS:VAL,TD:VAL,HEAD:VAL,ENL:VAL,ENR:VAL>

    def __init__(self):
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
            self.ser.flush()
        except Exception as e:
            print(f"[ERROR] Impossibile aprire la porta seriale: {e}")
            self.ser = None

        self.distanceFront = 9999.0
        self.distanceLeft  = 9999.0
        self.distanceRight = 9999.0
        self.heading       = 0.0
        self._encL         = 0
        self._encR         = 0

        self.running = True
        self.thread  = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    def _read_loop(self):
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

    def sendControl(self, offset, speed, shake=False):
        """
        Invia il pacchetto di controllo all'ESP32.
          offset : float  sterzo -1.0 … +1.0
          speed  : int    velocità (negativo = retromarcia per lo shake)
          shake  : bool   True se il robot è in modalità shake
        """
        if self.ser:
            sh  = 1 if shake else 0
            msg = f"<OFF:{round(offset, 2)},SPD:{int(speed)},SH:{sh}>\n"
            try:
                self.ser.write(msg.encode('utf-8'))
            except Exception:
                pass

    def getDistanceFront(self):  return self.distanceFront
    def getDistanceLeft(self):   return self.distanceLeft
    def getDistanceRight(self):  return self.distanceRight
    def getDistance(self):       return self.distanceFront
    def getHeading(self):        return self.heading

    def close(self):
        self.running = False
        if self.ser:
            self.ser.close()