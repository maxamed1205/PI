# programm to verifiy the i2c address of the device
#import SMBus
import sys
import time
import smbus2
import numpy as np

# bus = smbus2.SMBus(1)
# i2c_address = 0x68  # Example I2C address
# register = 0x01   # Temperature register
import smbus

# Initialize SMBus
i2c = smbus.SMBus(0)

# Accelerometer I2C address (replace with your accelerometer's address)
ACCELEROMETER_ADDRESS = 0x68  # Example: 0x1D

# Register addresses for X, Y, and Z acceleration (replace with your accelerometer's register addresses)
ACC_X_REGISTER = 0x00
ACC_Y_REGISTER = 0x01
ACC_Z_REGISTER = 0x02

# Read the accelerometer data
try:
  acc_x = i2c.read_byte_data(ACCELEROMETER_ADDRESS, ACC_X_REGISTER)
  acc_y = i2c.read_byte_data(ACCELEROMETER_ADDRESS, ACC_Y_REGISTER)
  acc_z = i2c.read_byte_data(ACCELEROMETER_ADDRESS, ACC_Z_REGISTER)

  # Print the data (interpret the data based on your accelerometer's datasheet)
  print(f"Acceleration X: {acc_x}")
  print(f"Acceleration Y: {acc_y}")
  print(f"Acceleration Z: {acc_z}")

except IOError:
  print("Error: Could not communicate with accelerometer.")

# def get_i2c_address(bus_num, i2c_addr):
#     try:
#         bus = SMBus(bus_num)
#         bus.write_byte(i2c_addr, 0)
#         bus.close()
#         return True
#     except IOError:
#         return False
#     except Exception as e:
#         print("Error: " + str(e))
#         return False
#
# def find_i2c_address(bus_num, start_addr, end_addr):
#     found_addresses = []
#     for addr in range(start_addr, end_addr + 1):
#         if get_i2c_address(bus_num, addr):
#             found_addresses.append(addr)
#     return found_addresses
#
# def main():
#     bus_num = 1  # Change this to the appropriate bus number
#     start_addr = 0x03
#     end_addr = 0x77
#     found_addresses = find_i2c_address(bus_num, start_addr, end_addr)
#     if found_addresses:
#         print("Found I2C addresses:")
#         for addr in found_addresses:
#             print(hex(addr))  