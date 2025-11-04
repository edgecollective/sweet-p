import board
import struct
import time
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_24lc32
import adafruit_ds3231
import adafruit_displayio_ssd1306
from adafruit_rockblock import RockBlock
import digitalio
import sys
from analogio import AnalogIn

probe_power_pin = digitalio.DigitalInOut(board.D10)
probe_power_pin.direction = digitalio.Direction.OUTPUT
probe_power_pin.value = False

while True:
    probe_power_pin.value = False
    print("D10 off")
    time.sleep(5)
    probe_power_pin.value = True
    print("D10 on")
    time.sleep(5)
    
    

