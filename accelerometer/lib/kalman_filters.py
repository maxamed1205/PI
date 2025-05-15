import math
import time


class SimpleKalmanFilter:
    def __init__(self, q_angle=0.001, q_bias=0.003, r_measure=0.03):
        self.q_angle = q_angle
        self.q_bias = q_bias
        self.r_measure = r_measure

        self.angle = 0.0  # Estimation de l'angle
        self.bias = 0.0   # Biais du gyroscope
        self.P = [[0, 0], [0, 0]]  # Matrice de covariance

    def update(self, new_angle, new_rate, dt):
        # Prévision
        rate = new_rate - self.bias
        self.angle += dt * rate

        # Mise à jour de la covariance
        self.P[0][0] += dt * (dt*self.P[1][1] - self.P[0]
                              [1] - self.P[1][0] + self.q_angle)
        self.P[0][1] -= dt * self.P[1][1]
        self.P[1][0] -= dt * self.P[1][1]
        self.P[1][1] += self.q_bias * dt

        # Innovation
        S = self.P[0][0] + self.r_measure
        K = [self.P[0][0]/S, self.P[1][0]/S]

        y = new_angle - self.angle

        # Mise à jour avec mesure
        self.angle += K[0] * y
        self.bias += K[1] * y

        P00_temp = self.P[0][0]
        P01_temp = self.P[0][1]

        self.P[0][0] -= K[0] * P00_temp
        self.P[0][1] -= K[0] * P01_temp
        self.P[1][0] -= K[1] * P00_temp
        self.P[1][1] -= K[1] * P01_temp

        return self.angle
