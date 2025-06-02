#-----------------------------------------------------------------------------#
# file: read_angle.py
# author: Your Name
# date: 2023-10-01
# description: This class reads the angle from an IMU sensor with fusion 
#              sensors and applies a Madgwick filter for 
#              orientation estimation.
# version: 1.0
# Disclaimer: This code is for educational purposes only. Use at your own risk.
# Info: This system is designed to work with the BMI270 IMU sensor and requires 
#       the appropriate libraries and hardware setup. Ensure that the sensor is 
#       connected. The design of I2C used are defined by config in the 
#       raspberry pi 5 for the PI DispMed. Tu used it in another raspberry pi, 
#       you need this info:
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
# LIBRABRY IMPORTS
# --------------------------------------------------

import time
import math
import time

import numpy as np
from scipy.spatial.transform import Rotation as R
from ahrs.filters import Madgwick

from bmi270.BMI270 import *

# --------------------------------------------------
# CLASS CONFIGURATION
# --------------------------------------------------

class ReadAngle_IMU:
    def __init__(self, bus_num, i2c_addr=I2C_PRIM_ADDR):

        self.last_time = time.time()
        
        self.angle_distal = 0
        self.angle_proximal = 0
        
        self.data_array_acc = np.zeros((3,3), dtype=np.float32)
        self.data_array_gyr = np.zeros((3,3), dtype=np.float32)
        
        sensors_bus1 = self.create_sensor(bus_num[0], i2c_addr)
        sensors_bus11 = self.create_sensor(bus_num[1], i2c_addr)
        sensors_bus12 = self.create_sensor(bus_num[2], i2c_addr)

        self.sensors = sensors_bus1 + sensors_bus11 + sensors_bus12
        
        # Madgwick filters for each IMU
        # Adjust beta and zeta parameters based on expected dynamics 
        # and noise characteristics of the IMUs
        # There are defined by empiric trials
        # you can change them
        self.madgwick_filters = [
            Madgwick(beta=0.7, zeta=0.6, sampleperiod=0.01),
            Madgwick(beta=0.6, zeta=0.5, sampleperiod=0.01),
            Madgwick(beta=0.7, zeta=0.7, sampleperiod=0.01)
        ]
        # Store last quaternion for each IMU
        self.quaternions = [np.array([1.0, 0.0, 0.0, 0.0]) for _ in range(3)]
        
        # parameters for manage the drift and position of the IMUs
        self.calibration_quaternions = [None, None, None]
        self.gyro_bias = np.zeros((3, 3), dtype=np.float64)
        self.proximal_offset = 0.0
        self.distal_offset = 0.0
        
        # Low-pass filter 
        self.acc_lp = np.zeros((3, 3), dtype=np.float64)
        self.gyr_lp = np.zeros((3, 3), dtype=np.float64)
        # coefficient (0.1–0.3 typical)
        self.alpha = 0.2  

    
    def bmi270_init(self, bus_num, i2c_addr=I2C_PRIM_ADDR):
        try:
            bmi270 = BMI270(i2c_addr)
            bmi270.bus = SMBus(bus_num)
            bmi270.load_config_file()
        except Exception as e:
            print("Error: " + str(e))
            print("""Could not initialize bmi270. 
                  Check your wiring or try again.""")
            exit(1)
        # Parameters for the BMI270 sensor
        # Set the mode, ranges, ODRs, and filters
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
        """ Create and initialize a BMI270 sensor on the specified I2C bus.
        Args:
            bus_num (int): The I2C bus number to use (0, 1, or 2).
            i2c_addr (int): The I2C address of the BMI270 sensor.
        Returns:
            list: A list containing the initialized BMI270 sensor object.
        """
        sensors_bus = []
        sensor = self.bmi270_init(bus_num, i2c_addr)
        if sensor is not None:
            sensors_bus.append(sensor)
            return sensors_bus
        else:
            print("Error: Could not initialize sensor on bus ")
            sys.exit(1)
        return sensors_bus
    def convert_gyro_degree(self, gyro_data):
        """
        Read gyroscope angle in degrees
        """
        return gyro_data*(180 / math.pi)
       
    def read_angle(self):
        """ 
        Read angles from the IMUs and compute the relative angles.
        This method reads the accelerometer and gyroscope data from each IMU,
        applies a low-pass filter to the accelerometer data, and uses a 
        Madgwick filter to compute the orientation of each IMU. It then 
        calculates the relative angles between the IMUs based on their 
        orientations. It also applies a calibration offset to the proximal and 
        distal angles.
        
        Returns:
            tuple: A tuple containing the distal and 
            proximal angles in degrees.
        """
        current_time = time.time()
        dt = max(current_time - self.last_time, 1e-3)
        self.last_time = current_time

        try:
            for i, sensor in enumerate(self.sensors):
                # read accelerometer and gyroscope data from lib
                acc = np.array(sensor.get_acc_data(), dtype=np.float64)
                gyr = np.array(sensor.get_gyr_data(), dtype=np.float64)
                
                # Apply low-pass filter to accelerometer and gyroscope data
                self.acc_lp[i] = (self.alpha * acc + (1 - self.alpha) 
                * self.acc_lp[i])
                self.gyr_lp[i] = (self.alpha * gyr + (1 - self.alpha) 
                * self.gyr_lp[i])
                # convert accelerometer data to g's and subtract gyro bias
                acc_g = self.acc_lp[i] / 9.80665
                gyr = self.gyr_lp[i] - self.gyro_bias[i]

                # Check and reset quaternion if zero norm
                if np.linalg.norm(self.quaternions[i]) == 0:
                    self.quaternions[i] = np.array([1.0, 0.0, 0.0, 0.0])
                
                # Set actual dt
                self.madgwick_filters[i].sampleperiod = dt  
                q_new = self.madgwick_filters[i].updateIMU(
                    q=self.quaternions[i],
                    gyr=gyr,
                    acc=acc_g
                )
                # If filter returns None or zero-norm, reset
                if q_new is None or np.linalg.norm(q_new) == 0:
                    q_new = np.array([1.0, 0.0, 0.0, 0.0])

                self.quaternions[i] = q_new
                self.data_array_acc[i, :] = acc_g
                self.data_array_gyr[i, :] = gyr
            # Compute angles between IMUs (relative orientation)
            self.angle_proximal =self.relative_angle_between_quaternions(
                self.quaternions[0], self.quaternions[1]) -self.proximal_offset
            self.angle_distal = self.relative_angle_between_quaternions(
                self.quaternions[1], self.quaternions[2])- self.distal_offset

        except Exception as e:
            print("Error: " + str(e))
            print("""Could not send data. Check your wiring. 
                  Trying again in 5 seconds...""")
            time.sleep(5)

        return round(self.angle_distal), round(self.angle_proximal)


    def relative_angle_between_quaternions(self, q1, q2):
        """
        Compute the relative angle (in degrees) 
        between two orientations given as quaternions.
        """
        r1 = R.from_quat(q1)
        r2 = R.from_quat(q2)
        r_rel = r2 * r1.inv()
        angle = r_rel.magnitude() * (180/np.pi)
        return np.round(angle, 1)
    
    def calibrate_gyro_bias(self, samples=300, delay=0.005):
        """
        Calibrate gyroscope bias for each IMU.
        Place IMUs perfectly still, then call this function.
        Find the offset between the 3  IMUs dpeend of the one in the middle
        """
        print("Calibrating gyroscope bias... Please keep IMUs still.")
        bias = np.zeros((3, 3), dtype=np.float64)
        for s in range(samples):
            for i, sensor in enumerate(self.sensors):
                gyr = np.array(sensor.get_gyr_data(), dtype=np.float64)
                bias[i] += gyr
            time.sleep(delay)
        self.gyro_bias = bias / samples
    def calibrate_offsets(self,samples=100):
        """
        Place all IMUs in the reference position 
        (mechanically aligned as best as possible),
        then call this function to record the fixed offsets.
        This will calculate the offsets for the proximal and distal angles
        depend of mean values angles of the IMUs.
        This will average the angles over a number of samples
        to determine the offsets for the proximal and distal angles.
        Args:
            samples (int): Number of samples to average for calibration.
        Returns:
            None
        """
        sum_proximal = 0.0
        sum_distal = 0.0
        for _ in range(samples):
            angle_distal, angle_proximal = self.read_angle()
            sum_proximal += angle_proximal
            sum_distal += angle_distal
            time.sleep(0.01)
        self.proximal_offset = sum_proximal / samples
        self.distal_offset = sum_distal / samples