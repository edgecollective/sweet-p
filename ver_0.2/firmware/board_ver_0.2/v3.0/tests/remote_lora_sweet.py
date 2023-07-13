# SPDX-FileCopyrightText: 2018 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""CircuitPython Essentials Analog In example"""
import time
import board
import busio
import digitalio
import adafruit_rfm9x
from analogio import AnalogIn
import struct
from adafruit_max1704x import MAX17048
from adafruit_lc709203f import LC709203F, PackSize

i2c = board.I2C()
while not i2c.try_lock():
    pass
i2c_address_list = i2c.scan()
i2c.unlock()

device = None

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


#node-specific params
node_id = 2
relay_node = 11
base_node = 1

#analog_in = AnalogIn(board.A1)
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

ultrasonic_trigger = digitalio.DigitalInOut(board.D5)
ultrasonic_trigger.direction = digitalio.Direction.OUTPUT

uart = busio.UART(board.TX, board.RX, baudrate=9600)

# radio params
RADIO_FREQ_MHZ = 900.0
LORA_CS = digitalio.DigitalInOut(board.D6)
LORA_RESET = digitalio.DigitalInOut(board.D9)
spi = board.SPI()
rfm9x = adafruit_rfm9x.RFM9x(spi, LORA_CS, LORA_RESET, RADIO_FREQ_MHZ)
rfm9x.node = node_id
rfm9x.enable_crc = True
rfm9x.ack_delay = .1


def get_voltage(pin):
    return (pin.value * 3.3) / 65536

def get_depth():
    dm=""
    ultrasonic_trigger.value=False
    time.sleep(.5)
    ultrasonic_trigger.value=True
    time.sleep(.1)
    data = uart.read(32)
    if data is not None:
        led.value = True
        data_string = ''.join([chr(b) for b in data])
        d = data_string.split('\r')
        
        for i in d:
            if(len(i)==5):
                #print(i)
                dm=i.split('R')[1]
        led.value = False
    if len(dm)>1:
        return(int(dm))
    else:
        return(None)

def send(node_to,payload):
    rfm9x.destination = node_to
    if rfm9x.send_with_ack(payload):
        print("-->",node_to,payload)
        print("<--",node_to,"ACK")
    else:
        print("-->",node_to,payload)
    print("")

while True:
    depth=str(get_depth())
    #depth=str(100.)
    batt_volts=str(f"{device.cell_voltage:.2f}")
    if depth is not None:
        print("depth=",depth)
        #data = struct.pack("i",x)
        send_string=str(depth)+","+str(batt_volts)
        payload=bytes(send_string,"UTF-8")
        #payload=data
        #send(relay_node,payload)
        send(base_node,payload)
    time.sleep(3)