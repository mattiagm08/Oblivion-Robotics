import time
import sys
from stateMachine import StateMachine

"""
###########################################################################
# MAIN - ENTRY POINT                                                      #
###########################################################################
# Questo è il file principale da lanciare sulla Raspberry Pi.             #
# Inizializza la StateMachine e garantisce la sicurezza del robot         #
# gestendo l'arresto dei motori in ogni scenario di uscita.               #
###########################################################################
"""

def main():
    # INIZIALIZZAZIONE DELLA FSM E DI TUTTI I SISTEMI ASSOCIATI
    robot = StateMachine()
    
    try:
        robot.run()
        
    except KeyboardInterrupt:
        # GESTIONE DELL'INTERRUZIONE MANUALE (CTRL+C) PER UN ARRESTO SICURO
        print("\n[MAIN] Interruzione manuale: arresto del robot in corso...")

    except Exception as error:
        # GESTIONE DI QUALSIASI ALTRA ECCEZIONE NON PREVISTA DURANTE L'ESECUZIONE
        print(f"\n[MAIN] ERRORE CRITICO DI SISTEMA: {error}")

    finally:
        # RILASCIO DI TUTTE LE RISORSE E ARRESTO SICURO DEL ROBOT IN QUALSIASI CASO
        if 'robot' in locals():
            robot.stop()
        
        print("[MAIN] Risorse rilasciate. Programma terminato.")
        sys.exit(0)

if __name__ == "__main__":
    main()