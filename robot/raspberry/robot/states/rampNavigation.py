from .baseState import BaseState
from config import MAX_SPEED, MIN_SPEED


class RampNavigation(BaseState):
    """
    ###########################################################################
    # RAMP NAVIGATION - STATE                                                 #
    ###########################################################################
    # Gestisce il movimento su piani inclinati utilizzando il pitch dell'IMU  #
    # Adatta dinamicamente la velocità per compensare gravità e inerzia       #
    ###########################################################################
    """

    def __init__(self, stateMachine):
        super().__init__(stateMachine)

        # SOGLIA ANGOLARE PER CONSIDERARE ATTIVA UNA RAMPA (IN GRADI)
        self.pitch_threshold = 10.0

        # INCREMENTO DI POTENZA IN SALITA PER COMPENSARE LA GRAVITÀ
        self.extra_power = 40

    def execute(self):

        # LETTURA PITCH DALL'IMU TRAMITE INTERFACCIA BOARD
        pitch = self.sm.board.getPitch()

        # ACQUISIZIONE DATI LINEA DAL SISTEMA DI VISIONE
        data = self.sm.lineCam.getLineData()

        # SE L'INCLINAZIONE TORNA PROSSIMA A ZERO
        # CONSIDERIAMO TERMINATA LA RAMPA
        if abs(pitch) < 5.0:
            self.sm.logger.success("Tornato in piano. Ripristino LineFollow.")
            return "LINE_FOLLOW"

        # SE LA LINEA VIENE PERSA DURANTE LA RAMPA
        # TRANSIZIONE A GESTIONE GAP (CONDIZIONE CRITICA)
        if data is None or data['offset'] is None:
            return "GAP_CROSSING"

        # ##################################################################
        # CALCOLO VELOCITÀ ADATTIVA IN BASE ALL'INCLINAZIONE               #
        # ##################################################################

        if pitch > self.pitch_threshold:
            # SALITA RILEVATA
            # AUMENTO COPPIA PER SUPERARE RESISTENZA GRAVITAZIONALE
            self.sm.logger.warn(f"Salita rilevata ({pitch}°). Aumento coppia.")
            base_speed = MAX_SPEED + self.extra_power

        elif pitch < -self.pitch_threshold:
            # DISCESA RILEVATA
            # RIDUZIONE VELOCITÀ PER EVITARE ACCELERAZIONE ECCESSIVA
            self.sm.logger.warn(f"Discesa rilevata ({pitch}°). Freno motore attivo.")
            base_speed = MIN_SPEED - 20

        else:
            # INCLINAZIONE MODERATA
            # VELOCITÀ DI SICUREZZA
            base_speed = MIN_SPEED

        # ##################################################################
        # APPLICAZIONE CONTROLLO LINEA E LIMITI HARDWARE                   #
        # ##################################################################

        # OFFSET DELLA LINEA SEMPRE PRIORITARIO PER LA STABILITÀ DIREZIONALE
        offset = data['offset']

        # LIMITAZIONE VELOCITÀ AL MASSIMO CONSENTITO DAL PWM (0-255)
        final_speed = min(255, int(base_speed))

        # INVIO COMANDO DI CONTROLLO AL MICROCONTROLLORE
        self.sm.board.sendControl(offset, final_speed)

        return "RAMP_NAVIGATION"