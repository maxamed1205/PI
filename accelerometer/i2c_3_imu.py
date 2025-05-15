#!/usr/bin/env python3

# Program to read data from the BMI270 IMU
# Used for 3 IMUs connected to the same I2C bus
# PIN 1 : SDA-1
# PIN 2 : SCL-1
# PIN 13 : SDA-0
# PIN 14 : SCL-0
# PIN 32 / GPIO 12 : SDA-2
# PIN 33 / GPIO 13 : SCL-2
# To use imu on I2C-0
# Modifify in boot/firmware/config.txt
# dtpapram=i2c_vc=on
# for I2C-2
# dtoverlay=i2c2-pi5,pins_12_13

# ctrl i2c actif
# sudo i2cdetect -l : list all I2C buses
# sudo i2cdetect -y 1 : list all I2C devices on bus 1
# sudo i2cdetect -y 0 : list all I2C devices on bus 0
# sudo i2cdetect -y 2 : list all I2C devices on bus 2

import time
import math
import time

from bmi270.BMI270 import *
import lib.kalman_filters as kf
# from src.bmi270.BMI270 import *


# -------------------------------------------------
# INITIALIZATION & HARDWARE CONFIGURATION
# -------------------------------------------------
def bmi270_init(bus_num, i2c_addr):
    try:
        bmi270 = BMI270(i2c_addr)
        bmi270.bus = SMBus(bus_num)
        print("test")
        bmi270.load_config_file()
    except Exception as e:
        print("Error: " + str(e))
        print("Could not initialize bmi270. Check your wiring or try again.")
        exit(1)
    bmi270.set_mode(PERFORMANCE_MODE)
    bmi270.set_acc_range(ACC_RANGE_2G)
    bmi270.set_gyr_range(GYR_RANGE_1000)
    bmi270.set_acc_odr(ACC_ODR_200)
    bmi270.set_gyr_odr(GYR_ODR_200)
    bmi270.set_acc_bwp(ACC_BWP_OSR4)
    bmi270.set_gyr_bwp(GYR_BWP_OSR4)
    bmi270.disable_fifo_header()
    bmi270.enable_data_streaming()
    bmi270.enable_acc_filter_perf()
    bmi270.enable_gyr_noise_perf()
    bmi270.enable_gyr_filter_perf()

    return bmi270


# -------------------------------------------------
# CONSTANTS
# -------------------------------------------------
start_time = time.time()

# Initialiser les adresses des capteurs sur chaque bus


def create_sensor(bus_num, i2c_addr):
    sensors_bus = []
    sensor = bmi270_init(bus_num, i2c_addr)
    if sensor is not None:
        sensors_bus.append(sensor)
        return sensors_bus
    else:
        print("Error: Could not initialize sensor on bus ")
        sys.exit(1)
    return sensors_bus


# Initialiser les capteurs sur chaque bus
sensors_bus1 = create_sensor(0, I2C_PRIM_ADDR)
sensors_bus11 = create_sensor(1, I2C_PRIM_ADDR)
sensors_bus11 = create_sensor(3, I2C_PRIM_ADDR)

sensors = sensors_bus1 + sensors_bus11

# -------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------


def get_milliseconds():
    return int(round((time.time() - start_time) * 1000))


def get_and_send_data(sensor):
    # verif if recup in array or diff
    data_array_acc = np.zeros((3,3), dtype=np.int32)
    data_array_gyr = np.zeros((3,3), dtype=np.int32)
    data_time = 0

    data_time = get_milliseconds()
    data_array_acc = sensor.get_acc_data()  # (ax, ay, az) en m/s²
    data_array_gyr = sensor.get_gyr_data()        # (gx, gy, gz) en rad/s

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
    data_array_acc = np.zeros((3, 3), dtype=np.float32)
    data_array_gyr = np.zeros((3, 3), dtype=np.float32)

    # Initialiser deux filtres Kalman (un par IMU)
    kalman_filter1 = kf.SimpleKalmanFilter()
    kalman_filter2 = kf.SimpleKalmanFilter()
    kalman_filter3 = kf.SimpleKalmanFilter()
    # data_time = 0
    # Boucle principale
    last_time = time.time()
    while True:
        current_time = time.time() - start_time
        # now = time.time()
        dt = current_time - last_time
        last_time = current_time
        i = 0
        try:
            for sensor in sensors:
                data_array_acc[i, :], data_array_gyr[i,
                                                     :] = get_and_send_data(sensor)
                i += 1
            i = 0
        except Exception as e:
            print("Error: " + str(e))
            print("Could not send data. Check your wiring. Trying again in 5 seconds...")
            # data_streaming = False
            sleep(5)

        time_delta = current_time - old_time
        old_time = current_time

        pitch_acc1, roll_acc1 = acc_to_pitch_roll(data_array_acc[0, :])
        pitch_acc2, roll_acc2 = acc_to_pitch_roll(data_array_acc[1, :])
        pitch_acc3, roll_acc3 = acc_to_pitch_roll(data_array_acc[2, :])
        # Gyro X : rad/s -> deg/s
        gyro_x_deg_s_1 = data_array_gyr[0, 0] * (180 / math.pi)
        gyro_x_deg_s_2 = data_array_gyr[1, 0] * (180 / math.pi)
        gyro_x_deg_s_3 = data_array_gyr[2, 0] * (180 / math.pi)

        gyro_y_deg_s_1 = data_array_gyr[0, 1] * (180 / math.pi)
        gyro_y_deg_s_2 = data_array_gyr[1, 1] * (180 / math.pi)
        gyro_y_deg_s_3 = data_array_gyr[2, 1] * (180 / math.pi)

        gyro_z_deg_s_1 = data_array_gyr[0, 2] * (180 / math.pi)
        gyro_z_deg_s_2 = data_array_gyr[1, 2] * (180 / math.pi)
        gyro_z_deg_s_3 = data_array_gyr[2, 2] * (180 / math.pi)

        # Mise à jour du Kalman
        angle1 = kalman_filter1.update(roll_acc1, gyro_y_deg_s_1, dt)
        angle2 = kalman_filter2.update(roll_acc2, gyro_y_deg_s_2, dt)
        angle3 = kalman_filter3.update(roll_acc3, gyro_y_deg_s_3, dt)
        angle_rel = angle1 - angle2
        print(
            f"Angle 1: {angle1: .2f}°, angle 2 {angle2:.2f}°")
        print(f"Angle 3: {angle3:.2f}°")
        print(f"Angle relatif: {angle_rel:.2f}°")
        sleep(max(update_rate - time_delta, 0))


if __name__ == "__main__":
    main()
