from hx711_lgpio import HX711
import time

hx = HX711(dout_pin=27, pd_sck_pin=18)

print("Initialisation...")
time.sleep(1)

print("Stabilise ton capteur (ne touche pas)...")
time.sleep(2)

# Lire l'offset
offset = hx.get_raw_data_mean()
print(f"Offset mesuré (sans charge) : {offset}")

# Calibration avec un objet de 27g
input("Place ton objet de 27g sur le capteur puis appuie sur Entrée...")

valeur_avec_objet = hx.get_raw_data_mean()
print(f"Valeur brute avec l'objet : {valeur_avec_objet}")

poids_objet = 27  # grammes
facteur_etalonnage = (valeur_avec_objet - offset) / poids_objet
print(f"Facteur d'étalonnage : {facteur_etalonnage:.2f} points par gramme")

print("\nMesure en temps réel (force en Newtons) :")

try:
    while True:
        valeur_brute = hx.get_raw_data_mean()
        poids_estime = (valeur_brute - offset) / facteur_etalonnage  # en grammes
        force_estimee = (poids_estime / 1000) * 9.81  # en Newtons
        print(f"Force estimée : {force_estimee:.4f} N")
        time.sleep(0.5)
except KeyboardInterrupt:
    print("Arrêt du programme.")
    hx.cleanup()
