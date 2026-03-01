import datetime

class Logger:
    """
    ###########################################################################
    # UTILS: LOGGER COLORATO                                                  #
    ###########################################################################
    # Permette di distinguere visivamente messaggi di stato, avvisi ed errori #
    # Utilizzando colori ANSI e formatting bold                               #
    ###########################################################################
    """

    # #########################################################################
    # COSTANTI COLORI ANSI PER DIFFERENZIAZIONE VISIVA                        #
    # #########################################################################
    HEADER = '\033[95m'   # MAGENTA PER TITOLI/STATO ATTUALE
    OKBLUE = '\033[94m'   # BLU PER INFO GENERALI
    OKGREEN = '\033[92m'  # VERDE PER SUCCESSO
    WARNING = '\033[93m'  # GIALLO PER AVVISI
    FAIL = '\033[91m'     # ROSSO PER ERRORI CRITICI
    ENDC = '\033[0m'      # RESET FORMATTING ANSI
    BOLD = '\033[1m'      # GRASSETTO PER EVIDENZIARE

    # #########################################################################
    # FUNZIONE AUSILIARIA: RITORNA ORA CORRENTE FORMATTATA                    #
    # #########################################################################
    def _get_time(self):
        return datetime.datetime.now().strftime("%H:%M:%S")

    # #########################################################################
    # METODO INFO: STAMPA MESSAGGI DI INFORMAZIONE                            #
    # #########################################################################
    def info(self, msg):
        print(f"[{self._get_time()}] {self.OKBLUE}[INFO]{self.ENDC} {msg}")

    # #########################################################################
    # METODO SUCCESS: STAMPA MESSAGGI DI SUCCESSO                             #
    # #########################################################################
    def success(self, msg):
        print(f"[{self._get_time()}] {self.OKGREEN}[ OK ]{self.ENDC} {msg}")

    # #########################################################################
    # METODO WARN: STAMPA MESSAGGI DI AVVISO                                  #
    # #########################################################################
    def warn(self, msg):
        print(f"[{self._get_time()}] {self.WARNING}[WARN]{self.ENDC} {msg}")

    # #########################################################################
    # METODO ERROR: STAMPA MESSAGGI DI ERRORE CRITICO                         #
    # #########################################################################
    def error(self, msg):
        print(f"[{self._get_time()}] {self.FAIL}{self.BOLD}[ERR ]{self.ENDC} {msg}")

    # #########################################################################
    # METODO STATE: INDICA IL CAMBIO DI STATO ATTUALE                         #
    # #########################################################################
    def state(self, state_name):
        print(f"[{self._get_time()}] {self.HEADER}{self.BOLD}=== STATO: {state_name} ==={self.ENDC}")