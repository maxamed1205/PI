#!/usr/bin/env python3


import socket
import time
import math
import time

from bmi270.BMI270 import *
import lib.kalman_filters as kf
# from src.bmi270.BMI270 import *


# -------------------------------------------------
# INITIALIZATION
# -------------------------------------------------

try:
    BMI270_1 = BMI270(I2C_PRIM_ADDR)
    BMI270_1.load_config_file()
except Exception as e:
    print("Error: " + str(e))
    print("Could not initialize BMI270_1. Check your wiring or try again.")
    exit(1)

# try:
#     BMI270_2 = BMI270(I2C_SEC_ADDR)
#     BMI270_2.load_config_file()
# except Exception as e:
#     print("Error: " + str(e))
#     print("Could not initialize BMI270_2. Check your wiring or try again.")
#     exit(1)


# -------------------------------------------------
# HARDWARE CONFIGURATION
# -------------------------------------------------

BMI270_1.set_mode(PERFORMANCE_MODE)
BMI270_1.set_acc_range(ACC_RANGE_2G)
BMI270_1.set_gyr_range(GYR_RANGE_1000)
BMI270_1.set_acc_odr(ACC_ODR_200)
BMI270_1.set_gyr_odr(GYR_ODR_200)
BMI270_1.set_acc_bwp(ACC_BWP_OSR4)
BMI270_1.set_gyr_bwp(GYR_BWP_OSR4)
BMI270_1.disable_fifo_header()
BMI270_1.enable_data_streaming()
BMI270_1.enable_acc_filter_perf()
BMI270_1.enable_gyr_noise_perf()
BMI270_1.enable_gyr_filter_perf()

# BMI270_2.set_mode(PERFORMANCE_MODE)
# BMI270_2.set_acc_range(ACC_RANGE_2G)
# BMI270_2.set_gyr_range(GYR_RANGE_1000)
# BMI270_2.set_acc_odr(ACC_ODR_200)
# BMI270_2.set_gyr_odr(GYR_ODR_200)
# BMI270_2.set_acc_bwp(ACC_BWP_OSR4)
# BMI270_2.set_gyr_bwp(GYR_BWP_OSR4)
# BMI270_2.disable_fifo_header()
# BMI270_2.enable_data_streaming()
# BMI270_2.enable_acc_filter_perf()
# BMI270_2.enable_gyr_noise_perf()
# BMI270_2.enable_gyr_filter_perf()


# -------------------------------------------------
# NETWORK CONFIGURATION
# -------------------------------------------------

# Change IP and port to your needs
RECEIVER_ADDRESS = ('192.168.1.2', 8000)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Setup sender address if needed (to always use the same sport as sender)
# SENDER_ADDRESS = ('192.168.1.1', 8001)
# sock.bind(SENDER_ADDRESS)


# -------------------------------------------------
# CONSTANTS
# -------------------------------------------------

start_time = time.time()


# -------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------

def get_milliseconds():
    return int(round((time.time() - start_time) * 1000))


def get_and_send_data():
    # verif if recup in array or diff
    data_array_acc = np.zeros(3, dtype=np.int32)
    data_array_gyr = np.zeros(3, dtype=np.int32)
    data_time = 0

    data_time = get_milliseconds()
    data_array_acc = BMI270_1.get_acc_data()  # (ax, ay, az) en m/s²
    data_array_gyr = BMI270_1.get_gyr_data()        # (gx, gy, gz) en rad/s

    # data_array_acc2 = np.zeros(3, dtype=np.int32)
    # data_array_gyr2 = np.zeros(3, dtype=np.int32)
    # data_time2 = 0

    # data_time2 = get_milliseconds()
    # data_array_acc2 = BMI270_2.get_acc_data()  # (ax, ay, az) en m/s²
    # data_array_gyr2 = BMI270_2.get_gyr_data()        # (gx, gy, gz) en rad/s

    return data_array_acc, data_array_gyr

# Calcul pitch avec accéléromètre (toujours en utilisant la gravité)


def acc_to_pitch_roll(acc):
    # verfi if ok separarte in 3 var
    x, y, z = acc
    pitch = math.atan2(x, math.sqrt(y**2 + z**2))
    roll = math.atan2(-y, z)
    return math.degrees(pitch), math.degrees(roll)

# -------------------------------------------------
# MAIN
# -------------------------------------------------


def main():
    current_time = 0.0
    old_time = 0.0
    update_rate = 0.005
    # data_streaming = False
    data_array_acc = np.zeros(3, dtype=np.int32)
    data_array_gyr = np.zeros(3, dtype=np.int32)

    # Initialiser deux filtres Kalman (un par IMU)
    kalman_filter1 = kf.SimpleKalmanFilter()

    # Boucle principale
    last_time = time.time()
    while True:
        current_time = time.time() - start_time
        # now = time.time()
        dt = current_time - last_time
        last_time = current_time

        try:
            data_array_acc, data_array_gyr = get_and_send_data()
        except Exception as e:
            print("Error: " + str(e))
            print("Could not send data. Check your wiring. Trying again in 5 seconds...")
            # data_streaming = False
            sleep(5)

        time_delta = current_time - old_time
        old_time = current_time

        z = data_array_acc[2]  # * 9.81  # Convertir en m/s²
        pitch_acc1, roll_acc1 = acc_to_pitch_roll(data_array_acc)

        # Gyro X : rad/s -> deg/s
        gyro_x_deg_s_1 = data_array_gyr[0] * (180 / math.pi)

        gyro_y_deg_s_1 = data_array_gyr[1] * (180 / math.pi)

        gyro_z_deg_s_1 = data_array_gyr[2] * (180 / math.pi)

        # Mise à jour du Kalman
        angle1 = kalman_filter1.update(pitch_acc1, gyro_x_deg_s_1, dt)
        print("Angle1: ", angle1)
        print("Gyro X: ", gyro_x_deg_s_1)
        print("Gyro Y: ", gyro_y_deg_s_1)
        print("Gyro Z: ", gyro_z_deg_s_1)
        print("Pitch: ", pitch_acc1)
        print("Roll: ", roll_acc1)
        print("Z: ", z)
        # print info in a csv file
        # with open('data.csv', 'a') as f:
        #     f.write(f"{angle1},{gyro_x_deg_s_1},{gyro_y_deg_s_1},{gyro_z_deg_s_1},{pitch_acc1},{roll_acc1},{z}\n")
        # Send data to receiver

        sleep(max(update_rate - time_delta, 0))


if __name__ == "__main__":
    main()
