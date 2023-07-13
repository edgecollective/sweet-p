# SPDX-FileCopyrightText: 2018 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""CircuitPython Essentials Analog In example"""
import time
import board
import busio
import digitalio
from analogio import AnalogIn

analog_in = AnalogIn(board.A1)
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

uart = busio.UART(board.TX, board.RX, baudrate=9600)

def get_voltage(pin):
    return (pin.value * 3.3) / 65536


while True:
    #print((get_voltage(analog_in),))
    
    data = uart.read(16)  # read up to 32 bytes
    # print(data)  # this is a bytearray type

    if data is not None:
        led.value = True

        # convert bytearray to string
        data_string = ''.join([chr(b) for b in data])
        #print(data_string)
        #print(data_string, end="\n")
        d = data_string.split('\r')
        #print(d)
        depth=""
        for i in d:
            if(len(i)==5):
                #print(i)
                depth=int(i.split('R')[1])
        print("depth=",depth)

        print("---")
        #print("\n")
        #distance = "hello "+data_string.replace('R','').strip()+" goodbye"
        #print(distance)
        #print("\n")

        led.value = False
        

