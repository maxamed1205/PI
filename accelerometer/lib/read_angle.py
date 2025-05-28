#-----------------------------------------------------------------------------#
# file: read_angle.py
# author: Your Name
# date: 2023-10-01
# description: This script reads the angle from an IMU sensor using Kalman filters
#              and processes the data to calculate the angles of different parts of a finger.
# Disclaimer: This code is for educational purposes only. Use at your own risk.
# Info: This system is designed to work with the BMI270 IMU sensor and requires the
#       appropriate libraries and hardware setup. Ensure that the sensor is connected.
#       The design of I2C used are defined by config in the raspberry pi 5 for
#       the PI DispMed. Tu used it in another raspberry pi, you need this info:
#       
#       Used for 3 IMUs connected to the same I2C bus
#       PIN 1 : SDA-1
#       PIN 2 : SCL-1
#       PIN 13 : SDA-0
#       PIN 14 : SCL-0
#       PIN 32 / GPIO 12 : SDA-2
#       PIN 33 / GPIO 13 : SCL-2
#       To use imu on I2C-0
#       Modifify in boot/firmware/config.txt
#       dtpapram=i2c_vc=on
#       for I2C-2
#       dtoverlay=i2c2-pi5,pins_12_13
        
#       ctrl i2c actif
#       sudo i2cdetect -l : list all I2C buses
#       sudo i2cdetect -y 1 : list all I2C devices on bus 1
#       sudo i2cdetect -y 0 : list all I2C devices on bus 0
#       sudo i2cdetect -y 2 : list all I2C devices on bus 2
#-----------------------------------------------------------------------------#

# --------------------------------------------------
# Classe pour lire les angles à partir d'accéléromètres BMI270
# --------------------------------------------------

import time                     # Module standard pour gérer le temps (utile pour le time.sleep ou time.time)
import math                     # Module standard pour les fonctions mathématiques comme les racines carrées ou les angles
import time                     # Import redondant (déjà importé plus haut), mais sans effet négatif

from bmi270.BMI270 import *     # Importe toutes les classes et constantes nécessaires depuis le module BMI270 personnalisé
import accelerometer.lib.kalman_filters as kf  # Importe le module de filtres de Kalman maison sous un alias court

class ReadAngle_IMU:
    def __init__(self, bus_num, i2c_addr=I2C_PRIM_ADDR):
        # Initialise un filtre de Kalman pour chaque capteur IMU (ici on suppose 3 IMU au total)
        self.kf1 = kf.SimpleKalmanFilter()  # Filtre pour IMU 1 (base)
        self.kf2 = kf.SimpleKalmanFilter()  # Filtre pour IMU 2 (proximal)
        self.kf3 = kf.SimpleKalmanFilter()  # Filtre pour IMU 3 (distal)

        self.last_time = time.time()        # Enregistre le temps actuel (servira pour des calculs de delta temps)

        self.angle_base = 0                 # Initialise l'angle mesuré par l'IMU de la base à 0°
        self.angle_distal = 0              # Initialise l'angle mesuré par l'IMU distal à 0°
        self.angle_proximal = 0            # Initialise l'angle mesuré par l'IMU proximal à 0°

        self.data_array_acc = np.zeros((3,3), dtype=np.int32)  # Matrice 3x3 pour stocker les données d'accélération (chaque ligne = IMU)
        self.data_array_gyr = np.zeros((3,3), dtype=np.int32)  # Matrice 3x3 pour stocker les données gyroscopiques

        sensors_bus1 = self.create_sensor(bus_num[0], i2c_addr)   # Initialise les capteurs sur le premier bus
        sensors_bus11 = self.create_sensor(bus_num[1], i2c_addr)  # Initialise les capteurs sur le second bus
        sensors_bus12 = self.create_sensor(bus_num[2], i2c_addr)  # Initialise les capteurs sur le troisième bus

        self.sensors = sensors_bus1 + sensors_bus11 + sensors_bus12  # Concatène tous les capteurs dans une seule liste

    def bmi270_init(self, bus_num, i2c_addr=I2C_PRIM_ADDR):
        try:
            bmi270 = BMI270(i2c_addr)         # Crée une instance du capteur BMI270 avec l’adresse I2C spécifiée
            bmi270.bus = SMBus(bus_num)       # Associe le bus I2C correspondant à cette instance
            bmi270.load_config_file()         # Charge la configuration nécessaire au bon fonctionnement du capteur
        except Exception as e:
            print("Error: " + str(e))          # Affiche l’erreur si l’initialisation échoue
            print("Could not initialize bmi270. Check your wiring or try again.")
            exit(1)                            # Quitte le programme avec un code d’erreur

        # Paramétrage du capteur pour des mesures précises
        bmi270.set_mode(PERFORMANCE_MODE)     # Active le mode performance (précision accrue)
        bmi270.set_acc_range(ACC_RANGE_2G)    # Définit la plage de mesure de l’accéléromètre à ±2g
        bmi270.set_gyr_range(GYR_RANGE_1000)  # Définit la plage du gyroscope à ±1000°/s
        bmi270.set_acc_odr(ACC_ODR_200)       # Définit la fréquence de l’accéléromètre à 200 Hz
        bmi270.set_gyr_odr(GYR_ODR_200)       # Définit la fréquence du gyroscope à 200 Hz
        bmi270.set_acc_bwp(ACC_BWP_OSR4)      # Définit la bande passante (filtrage) de l’accéléromètre
        bmi270.set_gyr_bwp(GYR_BWP_OSR4)      # Idem pour le gyroscope

        bmi270.disable_fifo_header()          # Désactive les entêtes FIFO (flux brut sans métadonnées)
        bmi270.enable_data_streaming()        # Active le streaming des données (acc + gyro en continu)
        bmi270.enable_acc_filter_perf()       # Active le filtre de performance pour l’accéléromètre
        bmi270.enable_gyr_noise_perf()        # Active la réduction de bruit du gyroscope
        bmi270.enable_gyr_filter_perf()       # Active également le filtre de performance du gyroscope

        return bmi270                         # Retourne l’objet BMI270 configuré
    def create_sensor(self, bus_num, i2c_addr):
        sensors_bus = []  # Initialise une liste vide pour stocker les capteurs connectés sur un bus donné
        sensor = self.bmi270_init(bus_num, i2c_addr)  # Tente d'initialiser un capteur sur le bus I2C spécifié
        if sensor is not None:  # Vérifie que le capteur a bien été initialisé
            sensors_bus.append(sensor)  # Ajoute le capteur à la liste
            return sensors_bus  # Retourne la liste contenant le capteur unique
        else:
            print("Error: Could not initialize sensor on bus ")  # Affiche un message d'erreur si l'initialisation échoue
            sys.exit(1)  # Termine le programme car le capteur est indispensable
        return sensors_bus  # (Code inatteignable ici, ajouté par sécurité)

    def convert_gyro_y_degree(self, gyro_data):
        return gyro_data * (180 / math.pi)  # Convertit les données gyroscopiques de radians vers degrés (axe Y uniquement)

    def pitch_roll_angle(self, accel_data):
        pitch = math.atan2(accel_data[1], math.sqrt(accel_data[0]**2 + accel_data[2]**2))  # Calcule le pitch à partir des données d'accélération
        roll = math.atan2(accel_data[0], math.sqrt(accel_data[1]**2 + accel_data[2]**2))   # Calcule le roll à partir des données d'accélération
        return math.degrees(pitch), math.degrees(roll)  # Retourne les deux angles en degrés

    def yaw_angle(self, gyro_data):
        yaw = math.atan2(gyro_data[2], math.sqrt(gyro_data[0]**2 + gyro_data[1]**2))  # Calcule le yaw à partir des données gyroscopiques
        return math.degrees(yaw)  # Retourne le yaw converti en degrés

    def read_angle(self):
        current_time = time.time()  # Récupère l'heure actuelle en secondes depuis l'époque Unix
        dt = current_time - self.last_time  # Calcule le temps écoulé depuis la dernière mesure
        self.last_time = current_time  # Met à jour la dernière mesure de temps

        try:
            for i, sensor in enumerate(self.sensors):  # Parcourt les trois capteurs IMU
                acc = sensor.get_acc_data()  # Récupère les données d'accélération du capteur i
                gyr = sensor.get_gyr_data()  # Récupère les données gyroscopiques du capteur i
                self.data_array_acc[i, :] = acc  # Stocke les données d'accélération dans le tableau
                self.data_array_gyr[i, :] = gyr  # Stocke les données gyroscopiques dans le tableau

            pitch_acc1, roll_acc1 = self.pitch_roll_angle(self.data_array_acc[0, :])  # Calcule pitch/roll pour IMU 1
            pitch_acc2, roll_acc2 = self.pitch_roll_angle(self.data_array_acc[1, :])  # Calcule pitch/roll pour IMU 2
            pitch_acc3, roll_acc3 = self.pitch_roll_angle(self.data_array_acc[2, :])  # Calcule pitch/roll pour IMU 3

            gyro_y_deg_s_1 = self.convert_gyro_y_degree(self.data_array_gyr[0, 1])  # Convertit le gyroscope Y de l’IMU 1
            gyro_y_deg_s_2 = self.convert_gyro_y_degree(self.data_array_gyr[1, 1])  # Convertit le gyroscope Y de l’IMU 2
            gyro_y_deg_s_3 = self.convert_gyro_y_degree(self.data_array_gyr[2, 1])  # Convertit le gyroscope Y de l’IMU 3

            angle_1 = self.kf1.update(roll_acc1, gyro_y_deg_s_1, dt)  # Filtrage Kalman pour l’IMU 1
            angle_2 = self.kf2.update(roll_acc2, gyro_y_deg_s_2, dt)  # Filtrage Kalman pour l’IMU 2
            angle_3 = self.kf3.update(roll_acc3, gyro_y_deg_s_3, dt)  # Filtrage Kalman pour l’IMU 3

            self.angle_distal = np.int32(np.round(abs(angle_3 - angle_2)))  # Différence entre IMU 2 et 3 = angle distal
            self.angle_proximal = np.int32(np.round(abs(angle_2 - angle_1)))  # Différence entre IMU 1 et 2 = angle proximal

        except Exception as e:
            print("Error: " + str(e))  # Affiche le message d'erreur
            print("Could not send data. Check your wiring. Trying again in 5 seconds...")  # Message de diagnostic
            sleep(5)  # Pause de 5 secondes avant une nouvelle tentative (en dehors de boucle principale)

        return self.angle_distal, self.angle_proximal  # Retourne les deux angles calculés pour les phalanges
