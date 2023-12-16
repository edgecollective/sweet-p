# SPDX-FileCopyrightText: 2020 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# Simple demo of printing the temperature from the first found DS18x20 sensor every second.
# Author: Tony DiCola

# A 4.7Kohm pullup between DATA and POWER is REQUIRED!

import time
import board
from adafruit_onewire.bus import OneWireBus
from adafruit_ds18x20 import DS18X20


# Initialize one-wire bus on board pin D5.
ow_bus = OneWireBus(board.D5)

# Scan for sensors and grab the first one found
sensor_list = ow_bus.scan()



# Main loop to print the temperature every second.
while True:
    for sensor in sensor_list:
        ds18 = DS18X20(ow_bus, sensor)
        print("Temperature: {0:0.3f}C".format(ds18.temperature))
        time.sleep(1.0)
