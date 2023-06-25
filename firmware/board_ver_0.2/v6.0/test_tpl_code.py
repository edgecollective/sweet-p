# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# pylint: disable=wrong-import-position
# CircuitPython / Blinka
import board
import busio
import struct
import digitalio
import time
from adafruit_debouncer import Debouncer
import adafruit_rfm9x
from adafruit_max1704x import MAX17048
from adafruit_lc709203f import LC709203F, PackSize
from adafruit_rockblock import RockBlock
import random
#import alarm
import sdcardio
import storage


print("SLEEPING A1")
time.sleep(.5)
#DONE pin
done_pin = digitalio.DigitalInOut(board.A1)
done_pin.direction = digitalio.Direction.OUTPUT
done_pin.value=True



    
