import sys
import os
import time

# Ajoute le chemin vers /accelerometer/lib/ à PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), 'accelerometer', 'lib'))

from orientation_angle import IMUOrientation, measure_angles

# Liste des bus I2C utilisés pour les 3 IMUs (proximal, intermédiaire, distal)
bus_list = [0, 1, 2]
imus = [IMUOrientation(bus) for bus in bus_list]

# Etape de calibration initiale
print("\n[INFO] Positionne le doigt en position de référence (repos, angle 0°).")
input("[ENTRÉE] pour lancer la calibration initiale...")

for i, imu in enumerate(imus):
    print(f"  ↪️  Calibration de l'IMU {i+1} (bus {bus_list[i]})...")
    imu.calibrate()
    print(f"  ✅ IMU {i+1} calibrée.")

print("\n✅ Calibration complète. Tu peux maintenant bouger le dispositif.")
print("📈 Les angles sont mesurés par rapport à cette position initiale.\n")

last_pip = None
last_dip = None

# Boucle principale de mesure temps réel
try:
    while True:
        angle_pip, angle_dip = measure_angles(imus)

        if last_pip is None or abs(angle_pip - last_pip) >= 1.0 or abs(angle_dip - last_dip) >= 1.0:
            print(f"➡️  PIP : {angle_pip:.1f}°   |   DIP : {angle_dip:.1f}°")
            last_pip = angle_pip
            last_dip = angle_dip
    time.sleep(0.1)

except KeyboardInterrupt:
    print("\n[FIN] Arrêt par utilisateur.")
