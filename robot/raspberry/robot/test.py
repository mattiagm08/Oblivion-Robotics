from picamera2 import Picamera2

# Inizializza la camera
picam2 = Picamera2()

# Configurazione (Risoluzione di anteprima)
config = picam2.create_preview_configuration(main={"size": (1280, 720)})
picam2.configure(config)

# Avvia l'anteprima in una finestra sul desktop
picam2.start_preview()

print("Anteprima avviata. Premi Invio nel terminale per chiudere.")
input() 

picam2.stop_preview()