# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
This example uses adafruit_display_text.label to display text using a custom font
loaded by adafruit_bitmap_font
"""

import board
import displayio
import terminalio
import struct
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font
import time
import digitalio
import adafruit_displayio_ssd1306
displayio.release_displays()
import alarm
from adafruit_rockblock import RockBlock
from analogio import AnalogIn
analog_in = AnalogIn(board.A1)
vbat_voltage = AnalogIn(board.VOLTAGE_MONITOR)

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT
led.value = False

sleep_time=60 # seconds

#DISPLAY
i2c = board.I2C()  # uses board.SCL and board.SDA
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)

WIDTH = 128
HEIGHT = 32  # Change to 64 if needed

display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=WIDTH, height=HEIGHT)



text = "Starting up ..."
font = terminalio.FONT
text_area = label.Label(font, text=text,scale=1,line_spacing=.9)

# Set the location
text_area.x = 5
text_area.y = 5

display.show(text_area)


# SAT MODEM
sat_power_pin = digitalio.DigitalInOut(board.A1)
sat_power_pin.direction = digitalio.Direction.OUTPUT
sat_power_pin.value = True
time.sleep(1)

uart = board.UART()
uart.baudrate = 19200

rb = RockBlock(uart)

text_area.text=rb.model

attempt=1

def get_voltage(pin):
    return (pin.value * 3.3) / 65536

def get_depth_inches(pin):
    return (pin.value * 3.3) / 65536 * 1000  / 3.2 / 2.54
    
def get_depth_meters(pin):
    return (pin.value * 3.3) / 65536 * 1000  / 3.2 / 100
    
while True:
    sat_power_pin.value = True
    time.sleep(2)
    batt_voltage= get_voltage(vbat_voltage)*2 #voltage divider on A9
    depth_meters = get_depth_meters(analog_in)
    
    print("batt_voltage=",batt_voltage)
    print("depth_meters=",depth_meters)
    
    data = struct.pack("f",batt_voltage)
    data += struct.pack("f",depth_meters)
    data += struct.pack("i",attempt)
    rb.data_out = data

    print("Talking to satellite...")
    status=rb.satellite_transfer()
    text_area.text=str(status)
    print(attempt,status)
    
    while status[0] > 8:
        time.sleep(10)
        attempt=attempt+1
        
        batt_voltage= get_voltage(vbat_voltage)*2 #voltage divider on A9
        depth_meters = get_depth_meters(analog_in)
        data = struct.pack("f",batt_voltage)
        data += struct.pack("f",depth_meters)
        data += struct.pack("i",attempt)
        rb.data_out = data
        
        status=rb.satellite_transfer()
        print(attempt, status)
        text_area.text=str(status)+"\nattempt "+str(attempt)
        time.sleep(1)

    text_area.text="DONE\nsleeping..."
    time.sleep(1)
    sat_power_pin.value = False
    
    #for i in range(sleep_time,0,-1):
    #    text_area.text="Next loop in:\n"+str(i)+" sec"
    #    time.sleep(1)
    
    #for i in range(sleep_time,0,-1):
    #    led.value = True
    #    time.sleep(.2)
    #    led.value = False
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + sleep_time)
    alarm.exit_and_deep_sleep_until_alarms(time_alarm)

