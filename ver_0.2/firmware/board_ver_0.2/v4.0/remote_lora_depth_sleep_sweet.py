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
import alarm

sleep_interval_sec = 60*5 #five minutes

#node-specific params
node_id = 2
base_node = 1
measure_interval_sec=2

#LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

#ultrasonic trigger
ultrasonic_trigger = digitalio.DigitalInOut(board.D5)
ultrasonic_trigger.direction = digitalio.Direction.OUTPUT

# set up the button
pin = digitalio.DigitalInOut(board.A0)
pin.direction = digitalio.Direction.INPUT
pin.pull = digitalio.Pull.UP
switch = Debouncer(pin)

#satellite power pin
sat_power_pin = digitalio.DigitalInOut(board.A1)
sat_power_pin.direction = digitalio.Direction.OUTPUT
sat_power_pin.value = True

#print("satellite powered")
#time.sleep(5)
#sat_power_pin.value=False
#print("satellite off")
#time.sleep(3)

# set up the fuel gauge
i2c = board.I2C()
while not i2c.try_lock():
    pass
i2c_address_list = i2c.scan()
i2c.unlock()

device = None

try:
    if 0x0b in i2c_address_list:
        lc709203 = LC709203F(board.I2C())
        # Update to match the mAh of your battery for more accurate readings.
        # Can be MAH100, MAH200, MAH400, MAH500, MAH1000, MAH2000, MAH3000.
        # Choose the closest match. Include "PackSize." before it, as shown.
        lc709203.pack_size = PackSize.MAH400

        device = lc709203

    elif 0x36 in i2c_address_list:
        max17048 = MAX17048(board.I2C())

        device = max17048

    else:
        raise Exception("Battery monitor not found.")
except:
    print("problem with battery")

# ultrasonic uart
uart_ultra = busio.UART(board.TX, board.RX, baudrate=9600)

# radio params
RADIO_FREQ_MHZ = 900.0
LORA_CS = digitalio.DigitalInOut(board.D6)
LORA_RESET = digitalio.DigitalInOut(board.D9)
spi = board.SPI()
rfm9x = adafruit_rfm9x.RFM9x(spi, LORA_CS, LORA_RESET, RADIO_FREQ_MHZ)
rfm9x.node = node_id
rfm9x.enable_crc = True
rfm9x.ack_delay = .1
print("LoRa OK")

print("Ready...")

def get_depth():
    dm=""
    ultrasonic_trigger.value=False
    time.sleep(.5)
    ultrasonic_trigger.value=True
    time.sleep(.1)
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

while True:

    #depth=str(get_depth())
    current = time.monotonic()
    #if current - last_measure >= measure_interval_sec + rand_interval:
    last_measure = current
    rand_interval=random.randint(1,2)
    #depth=100
    depth_cm=str(get_depth())
    batt_volts="0"
    try:
        batt_volts=str(f"{device.cell_voltage:.2f}")
    except:
        print("batt measure error")
    if depth_cm is not None:
        print("")
        print("depth=",depth_cm)
        #data = struct.pack("i",x)
        send_string=str(depth_cm)+","+str(batt_volts)
        payload=bytes(send_string,"UTF-8")
        #payload=data
        #send(relay_node,payload)
        led.value=True
        send(base_node,payload)
        led.value=False
    rfm9x.sleep()
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + sleep_interval_sec)
    alarm.exit_and_deep_sleep_until_alarms(time_alarm)
    
