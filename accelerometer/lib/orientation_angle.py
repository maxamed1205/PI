# orientation_angle.py
# ----------------------------------------------
# Nouvelle version avec calibration initiale + lissage par moyenne glissante
# ----------------------------------------------

import numpy as np
import math
from bmi270.BMI270 import *
from smbus2 import SMBus
import time
from collections import deque  # Pour moyenne glissante

# Filtre Madgwick pour estimer un quaternion d'orientation
class MadgwickAHRS:
    def __init__(self, beta=0.1):
        self.beta = beta
        self.q = np.array([1.0, 0.0, 0.0, 0.0])

    def update_imu(self, gx, gy, gz, ax, ay, az, dt):
        q1, q2, q3, q4 = self.q
        norm = math.sqrt(ax*ax + ay*ay + az*az)
        if norm == 0:
            return
        ax /= norm
        ay /= norm
        az /= norm

        _2q1 = 2.0 * q1
        _2q2 = 2.0 * q2
        _2q3 = 2.0 * q3
        _2q4 = 2.0 * q4

        f1 = _2q2 * q4 - _2q1 * q3 - ax
        f2 = _2q1 * q2 + _2q3 * q4 - ay
        f3 = 1.0 - _2q2 * q2 - _2q3 * q3 - az

        J = np.array([[-_2q3, _2q4, -_2q1, _2q2],
                      [_2q2, _2q1, _2q4, _2q3],
                      [0, -4*q2, -4*q3, 0]])

        step = J.T @ np.array([f1, f2, f3])
        step /= np.linalg.norm(step)

        q_dot = 0.5 * self.quat_mult(self.q, np.array([0.0, gx, gy, gz])) - self.beta * step
        self.q += q_dot * dt
        self.q /= np.linalg.norm(self.q)

    def quat_mult(self, q, r):
        w1, x1, y1, z1 = q
        w2, x2, y2, z2 = r
        return np.array([
            w1*w2 - x1*x2 - y1*y2 - z1*z2,
            w1*x2 + x1*w2 + y1*z2 - z1*y2,
            w1*y2 - x1*z2 + y1*w2 + z1*x2,
            w1*z2 + x1*y2 - y1*x2 + z1*w2
        ])

    def get_rotation_matrix(self):
        w, x, y, z = self.q
        return np.array([
            [1 - 2*y*y - 2*z*z, 2*x*y - 2*z*w, 2*x*z + 2*y*w],
            [2*x*y + 2*z*w, 1 - 2*x*x - 2*z*z, 2*y*z - 2*x*w],
            [2*x*z - 2*y*w, 2*y*z + 2*x*w, 1 - 2*x*x - 2*y*y]
        ])

# Représentation d'une IMU individuelle
class IMUOrientation:
    def __init__(self, bus_num, address=0x68):
        self.sensor = BMI270(address)
        self.sensor.bus = SMBus(bus_num)
        self.sensor.load_config_file()
        self.sensor.set_mode(PERFORMANCE_MODE)
        self.sensor.set_acc_range(ACC_RANGE_2G)
        self.sensor.set_gyr_range(GYR_RANGE_1000)
        self.sensor.set_acc_odr(ACC_ODR_200)
        self.sensor.set_gyr_odr(GYR_ODR_200)
        self.sensor.enable_data_streaming()
        self.fusion = MadgwickAHRS()
        self.last_time = time.time()
        self.R_ref = np.identity(3)

    def update(self):
        acc = np.array(self.sensor.get_acc_data(), dtype=np.float32)
        gyr = np.radians(np.array(self.sensor.get_gyr_data(), dtype=np.float32))
        now = time.time()
        dt = now - self.last_time
        self.last_time = now
        self.fusion.update_imu(gyr[0], gyr[1], gyr[2], acc[0], acc[1], acc[2], dt)

    def get_rotation_matrix(self):
        return self.fusion.get_rotation_matrix()

    def calibrate(self):
        self.update()
        self.R_ref = self.get_rotation_matrix()

# Calcul de l'angle articulaire entre deux matrices de rotation
def angle_between_rotations(R1, R2):
    R_rel = R1.T @ R2
    trace = np.trace(R_rel)
    theta = math.acos(max(min((trace - 1) / 2, 1.0), -1.0))
    return math.degrees(theta)

# Buffers pour moyenne glissante des angles (taille = 5)
pip_history = deque(maxlen=3)
dip_history = deque(maxlen=3)

# Fonction de mesure des angles PIP et DIP avec calibrage + lissage
def measure_angles(imus):
    for imu in imus:
        imu.update()
    R1_rel = imus[0].R_ref.T @ imus[0].get_rotation_matrix()
    R2_rel = imus[1].R_ref.T @ imus[1].get_rotation_matrix()
    R3_rel = imus[2].R_ref.T @ imus[2].get_rotation_matrix()
    angle_pip = angle_between_rotations(R1_rel, R2_rel)
    angle_dip = angle_between_rotations(R2_rel, R3_rel)

    # Empêche les petites variations résiduelles si le dispositif est immobile
     # if len(pip_history) > 0 and abs(angle_pip - pip_history[-1]) < 0.5:
      #    angle_pip = pip_history[-1]

    #  if len(dip_history) > 0 and abs(angle_dip - dip_history[-1]) < 1:
    #    angle_dip = dip_history[-1]

    pip_history.append(angle_pip)
    dip_history.append(angle_dip)

    avg_pip = sum(pip_history) / len(pip_history)
    avg_dip = sum(dip_history) / len(dip_history)

    return avg_pip, avg_dip
