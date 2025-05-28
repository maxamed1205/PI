import math                      # Importe le module math pour les opérations mathématiques de base (non utilisé ici mais peut servir pour des extensions)
import time                      # Importe le module time, souvent utilisé pour mesurer les intervalles de temps (non utilisé dans cette classe)

# --------------------------------------------------
# Classe : SimpleKalmanFilter
# Objectif : Appliquer un filtre de Kalman simple pour corriger les mesures d’angle provenant d’un capteur inertiel
# --------------------------------------------------
class SimpleKalmanFilter:
    def __init__(self, q_angle=0.001, q_bias=0.003, r_measure=0.03):
        self.q_angle = q_angle          # Bruit de processus pour l’angle (incertitude sur l’évolution réelle de l’angle dans le temps)
        self.q_bias = q_bias            # Bruit de processus sur le biais (incertitude sur l'évolution du biais du gyroscope)
        self.r_measure = r_measure      # Bruit de mesure (incertitude sur la mesure réelle de l’angle issue du capteur)

        self.angle = 0.0                # Angle estimé (état corrigé à chaque itération)
        self.bias = 0.0                 # Estimation actuelle du biais du gyroscope (dérive à long terme)
        self.P = [[0, 0], [0, 0]]       # Matrice de covariance 2x2 qui représente l’incertitude de l’estimation (initialisée à 0)

    def update(self, new_angle, new_rate, dt):
        # --- Étape de prédiction (prediction step) ---

        rate = new_rate - self.bias     # Retire le biais estimé du gyroscope à la nouvelle mesure de vitesse angulaire
        self.angle += dt * rate         # Mise à jour de l’angle estimé en intégrant la vitesse corrigée

        # Mise à jour de la matrice de covariance (prend en compte l'évolution temporelle de l'incertitude)
        self.P[0][0] += dt * (dt*self.P[1][1] - self.P[0][1] - self.P[1][0] + self.q_angle)  # Mise à jour P00
        self.P[0][1] -= dt * self.P[1][1]                                                   # Mise à jour P01
        self.P[1][0] -= dt * self.P[1][1]                                                   # Mise à jour P10
        self.P[1][1] += self.q_bias * dt                                                   # Mise à jour P11 (le biais a sa propre incertitude évolutive)

        # --- Étape de mise à jour (update step) ---

        S = self.P[0][0] + self.r_measure  # Calcul de l’innovation (erreur attendue) : variance combinée de l’estimation et de la mesure
        K = [self.P[0][0]/S, self.P[1][0]/S]  # Calcul des gains de Kalman (facteurs de correction pour l’angle et le biais)

        y = new_angle - self.angle         # Innovation : différence entre la mesure reçue et l’estimation prédite

        # Mise à jour de l’estimation de l’angle et du biais à l’aide des gains de Kalman
        self.angle += K[0] * y             # Correction de l’angle
        self.bias += K[1] * y              # Correction du biais

        # Sauvegarde temporaire des anciennes valeurs de la matrice pour la mise à jour finale
        P00_temp = self.P[0][0]              # Copie temporairement la valeur de la cellule [0][0] de la matrice de covariance (incertitude sur l'angle seul)
        P01_temp = self.P[0][1]              # Copie temporairement la valeur de la cellule [0][1] de la matrice de covariance (corrélation entre angle et biais)

        # Mise à jour finale de la matrice de covariance en fonction des gains de Kalman
        self.P[0][0] -= K[0] * P00_temp       # Réduit l'incertitude sur l'angle selon le gain de Kalman appliqué
        self.P[0][1] -= K[0] * P01_temp       # Réduit la corrélation entre angle et biais (colonne 1)
        self.P[1][0] -= K[1] * P00_temp       # Réduit la corrélation entre biais et angle (ligne 1)
        self.P[1][1] -= K[1] * P01_temp       # Réduit l'incertitude sur le biais selon la mesure reçue

        return self.angle  # Retourne l’angle corrigé par le filtre, censé être plus précis et moins bruité que la mesure brute

