from .baseState import BaseState


class VictimSearch(BaseState):
    """
    ###########################################################################
    # VICTIM SEARCH - STATE (PLACEHOLDER)                                     #
    ###########################################################################
    # Stato placeholder: il robot entra nell'evacuation zone e si ferma.      #
    # Da implementare con la logica di ricerca vittime.                        #
    ###########################################################################
    """

    def execute(self):
        self.sm.board.sendControl(0, 0)
        return "VICTIM_SEARCH"