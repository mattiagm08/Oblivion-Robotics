import time
import sys
from hardware.boardComm import BoardComm
from sensors.lineCamera import LineCamera

from utils.logger import Logger

# IMPORT DEGLI STATI OPERATIVI DELLA FSM
from states.lineFollow import LineFollow
from states.gapCrossing import GapCrossing
from states.intersectionHandling import IntersectionHandling
from states.obstacleAvoidance import ObstacleAvoidance
from states.rampNavigation import RampNavigation
from states.seesawNavigation import SeesawNavigation
from states.evacuationZoneEnter import EvacuationZoneEnter
from states.victimSearch import VictimSearch

class StateMachine:
    """
    ###########################################################################
    # FINITE STATE MACHINE - FSM                                              #
    ###########################################################################
    # Gestisce:                                                               #
    # - Ciclo principale di esecuzione del robot                              #
    # - Transizioni tra stati operativi                                       #
    # - Accesso centralizzato ad hardware e sensori                           #
    # - Procedura di shutdown                                                 #
    ###########################################################################
    """

    def __init__(self):
        # INIZIALIZZAZIONE SISTEMA DI LOGGING
        self.logger = Logger()
        self.logger.info("Inizializzazione Robot...")

        try:
            # INIZIALIZZAZIONE INTERFACCIA DI COMUNICAZIONE CON ESP32
            self.board = BoardComm()

            # INIZIALIZZAZIONE TELECAMERA PER RILEVAMENTO LINEA
            self.lineCam = LineCamera(cameraIndex=0)

            # REGISTRAZIONE DI TUTTI GLI STATI NELLA TABELLA DI DISPATCH
            self.states = {
                "LINE_FOLLOW":            LineFollow(self),
                "GAP_CROSSING":           GapCrossing(self),
                "INTERSECTION_HANDLING":  IntersectionHandling(self),
                "OBSTACLE_AVOIDANCE":     ObstacleAvoidance(self),
                "RAMP_NAVIGATION":        RampNavigation(self),
                "SEESAW_NAVIGATION":      SeesawNavigation(self),
                "EVACUATION_ZONE_ENTER":  EvacuationZoneEnter(self),
                "VICTIM_SEARCH":          VictimSearch(self),
            }

            # STATO INIZIALE DEL ROBOT
            self.currentStateName = "LINE_FOLLOW"

            # FLAG DI CONTROLLO LOOP PRINCIPALE
            self.active = True

            self.logger.success("Sistemi inizializzati e sincronizzati.")

        except Exception as error:
            self.logger.error(f"Errore durante l'inizializzazione: {error}")
            sys.exit(1)

    def run(self):
        # #####################################################################
        # CICLO PRINCIPALE DELLA FSM ESEGUITO A CIRCA 50Hz (20ms)             #
        # #####################################################################
        self.logger.state(self.currentStateName)

        try:
            while self.active:
                # RECUPERO DELL'OGGETTO CORRISPONDENTE ALLO STATO CORRENTE
                stateObj = self.states.get(self.currentStateName)

                if not stateObj:
                    self.logger.error(f"Stato non trovato: {self.currentStateName}")
                    break

                # ESECUZIONE LOGICA DELLO STATO
                # OGNI STATO RESTITUISCE IL NOME DELLO STATO SUCCESSIVO
                # O None PER MANTENERE LO STESSO STATO
                nextStateName = stateObj.execute()

                # GESTIONE TRANSIZIONE DI STATO (CON CONTROLLO NULL)
                try:
                    nextStateName = stateObj.execute()
                except Exception as e:
                    self.logger.error(f"Errore nello stato {self.currentStateName}: {e}")
                    continue

                # SINCRONIZZAZIONE DEL LOOP A 50Hz (PERIODO 20ms)
                time.sleep(0.02)

        except KeyboardInterrupt:
            self.stop()

        except Exception as e:
            self.logger.error(f"Eccezione durante il loop FSM: {e}")
            self.stop()

    def stop(self):

        if self._stopped:
            return

        self._stopped = True
        self.logger.warn("Richiesta arresto robot...")

        self.active = False

        # STOP MOTORI
        if hasattr(self, 'board') and self.board:
            try:
                self.board.sendControl(0, 0)
                time.sleep(0.1)
            except:
                pass

        # CHIUSURA CAMERA
        if hasattr(self, 'lineCam') and self.lineCam:
            try:
                self.lineCam.release()
                self.logger.info("Camera rilasciata.")
            except Exception as e:
                self.logger.error(f"Errore chiusura camera: {e}")

        # CHIUSURA SERIAL
        if hasattr(self, 'board') and self.board:
            try:
                self.board.close()
                self.logger.info("Seriale chiusa.")
            except:
                pass

        self.logger.success("Robot arrestato con successo.")

if __name__ == "__main__":
    fsm = StateMachine()
    fsm.run()