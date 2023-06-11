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
#from adafruit_max1704x import MAX17048
#from adafruit_lc709203f import LC709203F, PackSize
import random
import alarm
#import wifi

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT


#node-specific params
node_id = 2
base_node = 1
measure_interval_sec=2

# radio params
RADIO_FREQ_MHZ = 900.0
LORA_CS = digitalio.DigitalInOut(board.D6)
LORA_RESET = digitalio.DigitalInOut(board.D9)
spi = board.SPI()
rfm9x = adafruit_rfm9x.RFM9x(spi, LORA_CS, LORA_RESET, RADIO_FREQ_MHZ)
rfm9x.node = node_id
rfm9x.enable_crc = True
rfm9x.ack_delay = .1
rfm9x.sleep()


neo_power = digitalio.DigitalInOut(board.NEOPIXEL_POWER)
neo_power.switch_to_input()

#tft_power = digitalio.DigitalInOut(board.TFT_I2C_POWER)
#tft_power.switch_to_input()

#wifi.radio.enabled=False

print("Ready...")

def get_depth():
    dm=""
    #ultrasonic_trigger.value=False
    #time.sleep(.5)
    #ultrasonic_trigger.value=True
    #time.sleep(.1)
    data = uart_ultra.read(32)
    if data is not None:
        #led.value = True
        data_string = ''.join([chr(b) for b in data])
        d = data_string.split('\r')
        
        for i in d:
            if(len(i)==5):
                #print(i)
                dm=i.split('R')[1]
        #led.value = False
    if len(dm)>1:
        return(int(dm))
    else:
        return(None)

def send(node_to,payload):
    rfm9x.destination = node_to
    #if rfm9x.send_with_ack(payload):
    #    print("-->",node_to,payload)
    #    print("<--",node_to,"ACK")
    #else:
    #    print("-->",node_to,payload)
    rfm9x.send(payload)
    print("-->",node_to,payload)

last_measure = time.monotonic()
rand_interval=random.randint(1,2)

#sleeptime
sleep_interval_sec = 5

#tft_power = digitalio.DigitalInOut(board.TFT_I2C_POWER)
while True:

    #tft_power.switch_to_output()
    print("awake")
    for i in range(0,5):
        print(i)
        time.sleep(1)
    #tft_power.switch_to_input()
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + sleep_interval_sec)
    alarm.exit_and_deep_sleep_until_alarms(time_alarm)
    
