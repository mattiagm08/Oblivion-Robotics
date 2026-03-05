from .baseState import BaseState
from config import MAX_SPEED, MIN_SPEED

class RampNavigation(BaseState):
    """
    ###########################################################################
    # RAMP NAVIGATION - STATE                                                 #
    ###########################################################################
    # Gestisce il movimento su piani inclinati senza utilizzare il pitch.    #
    # Mantiene velocità costante e controllo linea tramite offset.            #
    ###########################################################################
    """

    def __init__(self, stateMachine):
        super().__init__(stateMachine)
        self.base_speed = MIN_SPEED + 20  # Velocità sicura su rampa

    def execute(self):
        data  = self.sm.lineCam.getLineData()

        # LINEA PERSA → GAP CROSSING
        if data is None or data['offset'] is None:
            return "GAP_CROSSING"

        offset = data['offset']

        # MANTIENI VELOCITÀ COSTANTE SULLA RAMPA
        self.sm.board.sendControl(offset, self.base_speed)

        return "RAMP_NAVIGATION"