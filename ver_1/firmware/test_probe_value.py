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

probe_adc = AnalogIn(board.A2)

while True:
    probe_power_pin.value = False
    print("D10 off")
    probe_voltage = probe_adc.value / 65535 * probe_adc.reference_voltage
    print("probe_voltage=",probe_voltage)
    time.sleep(5)
    
    print("-----")
    
    probe_power_pin.value = True
    print("D10 on")
    probe_voltage = probe_adc.value / 65535 * probe_adc.reference_voltage
    print("probe_voltage=",probe_voltage)
    time.sleep(5)
    
    

