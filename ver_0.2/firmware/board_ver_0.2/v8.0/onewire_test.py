# Example to send a packet periodically between addressed nodes with ACK
# Author: Jerry Needell
#
import time
import alarm
import board
import busio
import digitalio
import adafruit_rfm9x
from adafruit_onewire.bus import OneWireBus
from adafruit_ds18x20 import DS18X20
import struct

ow_bus = OneWireBus(board.D10)
node_id = 1

while True:
    try:
        #print("-" * 40)
        sensor_list = ow_bus.scan()
        temps=str(node_id)+","
        for sensor in sensor_list:
            #print(sensor.rom)
            sensor_id=int(sensor.rom[2])
            #print("sensor_id:",sensor_id)
            #d=str(sensor.rom,"ascii")
            ds18 = DS18X20(ow_bus, sensor)
            this_temp="{0:0.3f}".format(ds18.temperature)
            #time.sleep(1)
            temps=temps+str(sensor_id)+","+this_temp+","
        print(temps)
            #print("Temperature: {0:0.3f}C".format(ds18.temperature))
        #payload=bytes(temps,"UTF-8")
        #print(payload)
        #payload = bytes("hello from node {}".format(rfm9x.node), "UTF-8")
        #send(3,payload)
    except Exception as e:
        print("error: ",e)

    time.sleep(1)

# Create a an alarm that will trigger 20 seconds from now.
#time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + transmit_interval)
# Exit the program, and then deep sleep until the alarm wakes us.
#alarm.exit_and_deep_sleep_until_alarms(time_alarm)
# Does not return, so we never get here.
