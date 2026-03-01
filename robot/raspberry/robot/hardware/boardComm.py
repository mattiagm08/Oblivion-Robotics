import serial
import threading
import time
from config import SERIAL_PORT, BAUD_RATE

class BoardComm:
    """
    ###########################################################################
    # SERIALE ESP32 - COMUNICAZIONE                                           #
    ###########################################################################
    # Gestisce l'invio dei comandi ai motori e la ricezione costante dei      #
    # dati sensori (ToF, IMU e Colore) tramite un thread dedicato.            #
    ###########################################################################
    """
    def __init__(self):
        # #####################################################################
        # FASE 1: APERTURA PORTA SERIALE                                      #
        # #####################################################################
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
            self.ser.flush()
        except Exception as e:
            print(f"[ERROR] Impossibile aprire la porta seriale: {e}")
            self.ser = None

        # #####################################################################
        # FASE 2: INIZIALIZZAZIONE VARIABILI SENSORI                          #
        # #####################################################################
        self.distance = 999.0
        self.pitch = 0.0
        self.is_silver = False
        
        # #####################################################################
        # FASE 3: CREAZIONE THREAD PER LETTURA CONTINUA                       #
        # #####################################################################
        self.running = True
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    def _read_loop(self):
        # #####################################################################
        # FASE 4: CICLO DI LETTURA CONTINUA                                   #
        # #####################################################################
        while self.running and self.ser:
            if self.ser.in_waiting > 0:
                try:
                    # LEGGE LA RIGA E VERIFICA CHE NON SIA VUOTA
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if not line: continue

                    # FORMATO ATTESO: "D:150,P:12.5,S:0" (DISTANZA, INCLINAZIONE, ARGENTO)
                    parts = line.split(',')
                    for p in parts:
                        if ":" in p:
                            key, value = p.split(":")
                            if key == "D": self.distance = float(value)
                            if key == "P": self.pitch = float(value)
                            if key == "S": self.is_silver = bool(int(value))
                except (ValueError, IndexError):
                    pass
                except Exception as e:
                    print(f"[SERIAL DEBUG] Errore lettura: {e}")
            time.sleep(0.01)

    def sendControl(self, offset, speed):
        # #####################################################################
        # FASE 5: INVIO COMANDI AL BOARD                                      #
        # #####################################################################
        if self.ser:
            # FORMATO SINCRONIZZATO: <off:VAL,spd:VAL>
            msg = f"<off:{round(offset, 2)},spd:{int(speed)}>\n"
            try:
                self.ser.write(msg.encode('utf-8'))
            except:
                pass

    def getDistance(self):
        return self.distance

    def getPitch(self):
        return self.pitch

    def getIsSilver(self):
        return self.is_silver

    def close(self):
        self.running = False
        if self.ser:
            self.ser.close()