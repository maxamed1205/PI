import lgpio
import time

class HX711:
    def __init__(self, dout_pin, pd_sck_pin, gain=128):
        self.dout_pin = dout_pin
        self.pd_sck_pin = pd_sck_pin
        self.handle = lgpio.gpiochip_open(0)  # Ouvre le contrôleur GPIO

        # Réclame les pins GPIO
        lgpio.gpio_claim_input(self.handle, self.dout_pin)  # Pin de données (entrée)
        lgpio.gpio_claim_output(self.handle, self.pd_sck_pin)  # Pin d'horloge (sortie)

        # Initialisation des variables internes
        self.GAIN = 0
        self.OFFSET = 0
        self.set_gain(gain)  # Définir le gain

    def set_gain(self, gain):
        # Fonction pour définir le gain du capteur
        if gain == 128:
            self.GAIN = 1
        elif gain == 64:
            self.GAIN = 3
        elif gain == 32:
            self.GAIN = 2

        # Réinitialiser la lecture du capteur après avoir configuré le gain
        lgpio.gpio_write(self.handle, self.pd_sck_pin, 0)
        self.read()

    def is_ready(self):
        # Vérifie si le capteur est prêt à fournir une lecture
        return lgpio.gpio_read(self.handle, self.dout_pin) == 0

    def read(self):
        # Fonction de lecture des données brutes depuis le capteur
        while not self.is_ready():
            time.sleep(0.001)  # Attente jusqu'à ce que le capteur soit prêt

        data = 0
        # Lire les 24 bits de données
        for _ in range(24):
            lgpio.gpio_write(self.handle, self.pd_sck_pin, 1)
            data = (data << 1) | lgpio.gpio_read(self.handle, self.dout_pin)
            lgpio.gpio_write(self.handle, self.pd_sck_pin, 0)

        # Appliquer le gain en fonction du mode
        for _ in range(self.GAIN):
            lgpio.gpio_write(self.handle, self.pd_sck_pin, 1)
            lgpio.gpio_write(self.handle, self.pd_sck_pin, 0)

        # Gestion du signe des données (si négatif)
        if data & 0x800000:
            data |= ~0xffffff

        return data

    def get_raw_data_mean(self, times=3):
        # Fonction pour obtenir la moyenne des données brutes
        sum_data = 0
        for _ in range(times):
            sum_data += self.read()
        return sum_data / times

    def zero(self):
        # Fonction pour calibrer le capteur (réinitialiser l'offset)
        self.OFFSET = self.get_raw_data_mean()

    def get_weight_mean(self, times=3):
        # Fonction pour obtenir le poids moyen (compte l'offset)
        return self.get_raw_data_mean(times) - self.OFFSET

    def cleanup(self):
        # Ferme la connexion avec le contrôleur GPIO
        lgpio.gpiochip_close(self.handle)

    def reset(self):
        # Réinitialise le capteur HX711 (réinitialise l'offset)
        self.zero()  # Remet à zéro l'offset
        time.sleep(1)  # Laisse le temps au capteur de se réinitialiser
        print("Capteur réinitialisé !")
