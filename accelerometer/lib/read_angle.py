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

# class to read the angle from the accelerometer
import time
import math
import time

from bmi270.BMI270 import *
import accelerometer.lib.kalman_filters as kf

class ReadAngle_IMU:
    def __init__(self, bus_num, i2c_addr=I2C_PRIM_ADDR):
        # Initialiser deux filtres Kalman (un par IMU)
        self.kf1 = kf.SimpleKalmanFilter()
        self.kf2 = kf.SimpleKalmanFilter()
        self.kf3 = kf.SimpleKalmanFilter()

        self.last_time = time.time()
        
        self.angle_base = 0
        self.angle_distal = 0
        self.angle_proximal = 0
        
        self.data_array_acc = np.zeros((3,3), dtype=np.int32)
        self.data_array_gyr = np.zeros((3,3), dtype=np.int32)
        
        sensors_bus1 = self.create_sensor(bus_num[0], i2c_addr)
        sensors_bus11 = self.create_sensor(bus_num[1], i2c_addr)
        sensors_bus12 = self.create_sensor(bus_num[2], i2c_addr)

        self.sensors = sensors_bus1 + sensors_bus11 + sensors_bus12
    
    def bmi270_init(self, bus_num, i2c_addr=I2C_PRIM_ADDR):
        try:
            bmi270 = BMI270(i2c_addr)
            bmi270.bus = SMBus(bus_num)
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
    def create_sensor(self, bus_num, i2c_addr):
        sensors_bus = []
        sensor = self.bmi270_init(bus_num, i2c_addr)
        if sensor is not None:
            sensors_bus.append(sensor)
            return sensors_bus
        else:
            print("Error: Could not initialize sensor on bus ")
            sys.exit(1)
        return sensors_bus
    def convert_gyro_y_degree(self, gyro_data):
        # Read gyroscope angle y in degrees
        return gyro_data*(180 / math.pi)
    def pitch_roll_angle(self, accel_data):
        # Calculate pitch angle from accelerometer data
        pitch = math.atan2(accel_data[1], math.sqrt(accel_data[0]**2 + accel_data[2]**2))
        roll = math.atan2(accel_data[0], math.sqrt(accel_data[1]**2 + accel_data[2]**2))
        return math.degrees(pitch), math.degrees(roll)
    def yaw_angle(self, gyro_data):
        # Read gyroscope angle z in degrees
        yaw = math.atan2(gyro_data[2], math.sqrt(gyro_data[0]**2 + gyro_data[1]**2))
        return math.degrees(yaw)
       
    def read_angle(self):
        # Get the current time
        current_time = time.time()
        # Calculate the time difference
        dt = current_time - self.last_time
        # Update the last time
        self.last_time = current_time
        
        try:
            for i, sensor in enumerate(self.sensors):
                acc = sensor.get_acc_data()
                gyr = sensor.get_gyr_data()
                self.data_array_acc[i, :] = acc
                self.data_array_gyr[i, :] = gyr
                
            pitch_acc1, roll_acc1 = self.pitch_roll_angle(self.data_array_acc[0, :])
            pitch_acc2, roll_acc2 = self.pitch_roll_angle(self.data_array_acc[1, :])
            pitch_acc3, roll_acc3 = self.pitch_roll_angle(self.data_array_acc[2, :])

            gyro_y_deg_s_1 = self.convert_gyro_y_degree(self.data_array_gyr[0, 1])
            gyro_y_deg_s_2 = self.convert_gyro_y_degree(self.data_array_gyr[1, 1])
            gyro_y_deg_s_3 = self.convert_gyro_y_degree(self.data_array_gyr[2, 1])

            # angle from the 3 imus
            angle_1 = self.kf1.update(roll_acc1, gyro_y_deg_s_1, dt)
            angle_2 = self.kf2.update(roll_acc2, gyro_y_deg_s_2, dt)
            angle_3 = self.kf3.update(roll_acc3, gyro_y_deg_s_3, dt)

            # Calculate the angles between the IMUs 
            # to find the angles of the phalanges
            self.angle_distal = np.int32(np.round(abs(angle_3 - angle_2)))
            self.angle_proximal = np.int32(np.round(abs(angle_3 - angle_1)))

        except Exception as e:
            print("Error: " + str(e))
            print("Could not send data. Check your wiring. Trying again in 5 seconds...")
            # data_streaming = False
            sleep(5)
                    
        return self.angle_distal, self.angle_proximal