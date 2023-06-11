# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# pylint: disable=wrong-import-position
# CircuitPython / Blinka
import board
import busio
import time
import alarm
import digitalio

sleep_interval_sec = 5

neo_power = digitalio.DigitalInOut(board.NEOPIXEL_POWER)
neo_power.switch_to_input()

sat_power = digitalio.DigitalInOut(board.A1)
sat_power.direction = digitalio.Direction.OUTPUT
sat_power.value=False

#i2c_power = digitalio.DigitalInOut(board.I2C_POWER)
#i2c_power.switch_to_input()

while True:

    #tft_power.switch_to_output()
    print("sat_on")
    sat_power.value=True
    for i in range(0,5):
        print(i)
        time.sleep(1)
    p#rint("sat_off")
    #sat_power.value=False
    for i in range(0,5):
        print(i)
        time.sleep(1)
        
    
    #time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + sleep_interval_sec)
    #alarm.exit_and_deep_sleep_until_alarms(time_alarm)
    
