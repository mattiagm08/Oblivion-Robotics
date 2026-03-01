from abc import ABC, abstractmethod

class BaseState(ABC):
    """
    ###########################################################################
    # BASE STATE - CLASS                                                      #
    ###########################################################################
    # Definisce l'interfaccia obbligatoria per ogni stato del robot.          #
    # Ogni stato derivato deve implementare il metodo execute.                #
    ###########################################################################
    """

    def __init__(self, stateMachine):
        # ##################################################################
        # INIZIALIZZAZIONE: RIFERIMENTO ALLA MACCHINA A STATI              #
        # ##################################################################
        self.sm = stateMachine

    @abstractmethod
    def execute(self):
        pass