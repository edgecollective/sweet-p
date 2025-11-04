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


while True:
    #probe_power_pin.value = False
    #print("D10 off")
    probe_voltage = probe_adc.value / 65535 * VREF
    
    probe_current = probe_voltage / 120. # mA
    #print("probe_voltage=",probe_voltage)
    
    depth = (probe_current - CURRENT_INIT) * CONVERSION # in mm
    
    #if depth < 0:
    #    depth = 0.0
    print(probe_voltage,probe_current,depth)
    
    #print(f"voltage:{probe_voltage:.2f}V; depth:{depth:.2f}mm")
   
    time.sleep(.2)
    
    #print("-----")
    
    #probe_power_pin.value = True
    #print("D10 on")
    #probe_voltage = probe_adc.value / 65535 * probe_adc.reference_voltage
    #print("probe_voltage=",probe_voltage)
    #time.sleep(5)
    
    

