# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# pylint: disable=wrong-import-position
import time
import struct
import alarm
import busio

# CircuitPython / Blinka
import board
import digitalio
from adafruit_rockblock import RockBlock
from analogio import AnalogIn

print("starting up ...")

#uart = board.UART()
#uart.baudrate = 19200

uart = busio.UART(board.D12, board.D11, baudrate=9600)


print("got here")

#sat_power_pin = digitalio.DigitalInOut(board.D5)
#sat_power_pin.direction = digitalio.Direction.OUTPUT
#sat_power_pin.value = True
time.sleep(1)
# via USB cable
# import serial
# uart = serial.Serial("/dev/ttyUSB0", 19200)



rb = RockBlock(uart)
print("created a uart")


def get_voltage(pin):
    return (pin.value * 3.3) / 65536

def get_depth_inches(pin):
    return (pin.value * 3.3) / 65536 * 1000  / 3.2 / 2.54
    
def get_depth_meters(pin):
    return (pin.value * 3.3) / 65536 * 1000  / 3.2 / 100
    
while True:

    print("booting up ...")
    # turn on the satellite modem
    #sat_power_pin.value = True
    time.sleep(2)
    # create some data
    #batt_voltage= get_voltage(vbat_voltage)*2 #voltage divider on A9
    #depth_inches = get_depth_meters(analog_in)
    batt_voltage=3.7
    depth_inches=2.
    #sht = adafruit_sht31d.SHT31D(i2c)
    #bmp = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
    print("voltage:",batt_voltage)
    print("depth:",depth_inches)
    
    #some_int = 2112
    #some_float = 42.123456789
    #some_text = "hello world"
    #text_len = len(some_text)

    # create binary data
    data = struct.pack("f",batt_voltage)
    data += struct.pack("f",depth_inches)
    #data += struct.pack("2f", sht.relative_humidity, sht.temperature)
    #data += struct.pack("2f", bmp.pressure, bmp.temperature)
    #data += struct.pack("i", some_int)
    #data += struct.pack("f", some_float)
    #data += struct.pack("i", len(some_text))
    #data += struct.pack("{}s".format(text_len), some_text.encode())

    # put data in outbound buffer
    rb.data_out = data

    # try a satellite Short Burst Data transfer
    print("Talking to satellite...")
    status = rb.satellite_transfer()
    # loop as needed
    retry = 0
    while status[0] > 8:
        time.sleep(10)
        status = rb.satellite_transfer()
        print(retry, status)
        #print("signal_quality:",rb.signal_quality())
        retry += 1

    print("\nDONE.")

    # turn off the satellite modem
    #sat_power_pin.value = False

    #time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + 60*15)
    #pin_alarm = alarm.pin.PinAlarm(board.D10, False)

    # Deep sleep until one of the alarm goes off. Then restart the program.
    #alarm.exit_and_deep_sleep_until_alarms(time_alarm, pin_alarm)
    #alarm.exit_and_deep_sleep_until_alarms(time_alarm)
