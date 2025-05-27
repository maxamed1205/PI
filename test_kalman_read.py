import sys
import os
import time

# Ajouter le chemin vers le dossier contenant read_angle.py
sys.path.append(os.path.join(os.path.dirname(__file__), 'accelerometer', 'lib'))

from read_angle import ReadAngle_IMU

# Buses I2C utilisées
bus_list = [0, 1, 2]
imu_reader = ReadAngle_IMU(bus_list)

print("\n✅ Lecture des angles en cours (Kalman)")
print("➡️  Ctrl+C pour arrêter\n")

try:
    while True:
        angle_dist, angle_prox = imu_reader.read_angle()
        print(f"➡️  PIP : {angle_prox:.1f}°   |   DIP : {angle_dist:.1f}°")
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n[FIN] Arrêt par utilisateur.")
