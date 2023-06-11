# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# pylint: disable=wrong-import-position
# CircuitPython / Blinka
import board
import busio
import struct
import digitalio
import time

uart = busio.UART(board.D12, board.D11, baudrate=19200)
#uart = board.UART()
#uart.baudrate = 19200

# via USB cable
# import serial
# uart = serial.Serial("/dev/ttyUSB0", 19200)

from adafruit_rockblock import RockBlock


sat_power_pin = digitalio.DigitalInOut(board.A1)
sat_power_pin.direction = digitalio.Direction.OUTPUT
sat_power_pin.value = True
time.sleep(3)



rb = RockBlock(uart)

print(rb.model)

depth_cm=300
batt_volts=3.3
attempt=1

data = struct.pack("f",batt_volts)
data += struct.pack("i",depth_cm)
data += struct.pack("i",attempt)
rb.data_out = data

print("pausing...")
time.sleep(3)

print("Talking to satellite...")
status=rb.satellite_transfer()
print(attempt,status)

while status[0] > 8:
    time.sleep(10)
    status=rb.satellite_transfer()
    print(attempt, status)
    #text_area.text=str(status)+"\nattempt "+str(attempt)
    time.sleep(1)

print("DONE")
