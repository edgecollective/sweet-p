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

#node-specific params
node_id = 2
relay_node = 11
base_node = 1

#analog_in = AnalogIn(board.A1)
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

uart = busio.UART(board.TX, board.RX, baudrate=9600)

# radio params
RADIO_FREQ_MHZ = 900.0
LORA_CS = digitalio.DigitalInOut(board.D11)
LORA_RESET = digitalio.DigitalInOut(board.D6)
spi = board.SPI()
rfm9x = adafruit_rfm9x.RFM9x(spi, LORA_CS, LORA_RESET, RADIO_FREQ_MHZ)
rfm9x.node = node_id
rfm9x.enable_crc = True
rfm9x.ack_delay = 0.1


def get_voltage(pin):
    return (pin.value * 3.3) / 65536

def get_depth():
    depth=""
    data = uart.read(32)
    if data is not None:
        led.value = True
        data_string = ''.join([chr(b) for b in data])
        d = data_string.split('\r')
        
        for i in d:
            if(len(i)==5):
                #print(i)
                depth=i.split('R')[1]
        led.value = False
    if len(depth)>1:
        return(int(depth))
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
    #x=get_depth()
    x="10"
    if x is not None:
        print("depth=",x)
        #data = struct.pack("i",x)
        payload=bytes(str(x),"UTF-8")
        #payload=data
        #send(relay_node,payload)
        send(base_node,payload)
    time.sleep(3)