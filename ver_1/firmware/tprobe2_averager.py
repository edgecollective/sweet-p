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

DEPTH_RANGE = 5000.  # Depth measuring range 5000mm (for water)
CURRENT_RANGE = 16. # usable current range in mA
CURRENT_INIT = 4.00  # Current @ 0mm (unit: mA)
VREF = 3.3*1000  # ADC's reference voltage in mV, typical for CircuitPython boards: 3.3V

DENSITY_WATER = 1  # Pure water density normalized to 1

probe_power_pin = digitalio.DigitalInOut(board.D10)
probe_power_pin.direction = digitalio.Direction.OUTPUT
probe_power_pin.value = True

probe_adc = AnalogIn(board.A2)

CONVERSION = (DEPTH_RANGE / CURRENT_RANGE) / DENSITY_WATER

# 1 hPa = 10.2 mm water
NUM_AVE = 10
TIME_SPACING = 1

ave_depth_previous=0.

time.sleep(5) #needs warmup for sensor to turn on

while True:

    ave_depth=0.
    
    for i in range(0,NUM_AVE):
        
        #probe_power_pin.value = False
        #print("D10 off")
        probe_voltage = probe_adc.value / 65535 * VREF
        
        probe_current = probe_voltage / 120. # mA
        #print("probe_voltage=",probe_voltage)
        
        depth = (probe_current - CURRENT_INIT) * CONVERSION # in mm
        
        ave_depth=ave_depth+depth
        #if depth < 0:
        #    depth = 0.0
        print(probe_voltage,probe_current,depth,ave_depth_previous)
        
        #print(f"voltage:{probe_voltage:.2f}V; depth:{depth:.2f}mm")
       
        time.sleep(TIME_SPACING)
        
    ave_depth=ave_depth/float(NUM_AVE)
    ave_depth_previous=ave_depth
    
    #print(ave_depth)
    

