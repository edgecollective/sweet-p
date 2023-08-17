# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# pylint: disable=wrong-import-position
# CircuitPython / Blinka
import board
import busio
import struct
import digitalio
import time
#from adafruit_debouncer import Debouncer
import adafruit_rfm9x
from adafruit_rockblock import RockBlock
import random
#import alarm
import sdcardio
import storage
import analogio

vbat_voltage = analogio.AnalogIn(board.A0)

def get_voltage(pin):
    return (pin.value * 2.57) / 51000
#    return (pin.value)

spi = board.SPI()
cs = board.D10
sdcard = sdcardio.SDCard(spi, cs)
vfs = storage.VfsFat(sdcard)

storage.mount(vfs, "/sd")

send_count = 10 # how many wakeups before sending

max_sat_send_attempts = 20 

index = -1

sleep_interval_sec = 60*5 #five minutes

#node-specific params
node_id = 2
base_node = 1
measure_interval_sec=2

#LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# set up the button
#pin = digitalio.DigitalInOut(board.A0)
#pin.direction = digitalio.Direction.INPUT
#pin.pull = digitalio.Pull.UP
#switch = Debouncer(pin)


# ultrasonic uart
uart_ultra = busio.UART(board.TX, board.RX, baudrate=9600)

# radio params
RADIO_FREQ_MHZ = 900.0
LORA_CS = digitalio.DigitalInOut(board.D6)
LORA_RESET = digitalio.DigitalInOut(board.D9)

rfm9x = adafruit_rfm9x.RFM9x(spi, LORA_CS, LORA_RESET, RADIO_FREQ_MHZ)
rfm9x.node = node_id
rfm9x.enable_crc = True
rfm9x.ack_delay = .1
print("LoRa OK")

print("Ready...")

def get_depth():
    dm=""
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

rand_interval=random.randint(1,2)

index = -1


# get the last index value
with open("/sd/log.txt", "r") as f:
    lines = f.readlines()
    #for line in lines:
    #    print(line)
    last_line = lines[-1]
    j = last_line.split(' ')[0]
    #print(lines[-1])

index = int(j) + 1
print("index=",index)
#time.sleep(1)

my_batt=0
my_depth=0
#depth=100

depth_cm=get_depth()
if depth_cm is not None:
    my_depth=depth_cm
    

battery_voltage = get_voltage(vbat_voltage)*2 #voltage divider
my_batt=battery_voltage


with open("/sd/log.txt", "a") as f:
    print("%d %0.1f %d\n" % (index,my_batt,my_depth))
    f.write("%d %0.1f %d\n" % (index,my_batt,my_depth))
    led.value = False  # turn off LED to indicate we're done

sat_send_status=32

attempt=0

sat_power_pin = digitalio.DigitalInOut(board.A1)
sat_power_pin.direction = digitalio.Direction.OUTPUT
uart = busio.UART(board.D12, board.D11, baudrate=19200)

if(index%send_count==0): # then send satellite data

    
    attempt=1

    max_num_sat_connect_attempts = 4
    connect_attempt = 0
    


    sat_power_pin.value = True
    print("satellite powered")
    #time.sleep(3)
    
    sat_connect_success=False
    
    while (connect_attempt < max_num_sat_connect_attempts) and (sat_connect_success==False):  
        try:
            #satellite power pin  
            #print("about to try to get to uart")     
            time.sleep(1)
            rb = RockBlock(uart)
            
            #print("got to uart")
            time.sleep(1)
            print(rb.model)
            
            sat_connect_success=True
        except Exception as error:
            # handle the exception
            print("Connecting error:", error)
        
        connect_attempt=connect_attempt+1
            
            
    if(sat_connect_success==True):
        try:
            
            data = struct.pack("f",my_batt)
            data += struct.pack("i",my_depth)
            data += struct.pack("i",attempt)
            rb.data_out = data

            print("Talking to satellite...")
            status=rb.satellite_transfer()
            print(attempt,status)

            while status[0] > 8 and attempt<max_sat_send_attempts:
                time.sleep(10)
                status=rb.satellite_transfer()
                print(attempt, status)
                #text_area.text=str(status)+"\nattempt "+str(attempt)
                time.sleep(1)
                attempt=attempt+1
            #print("SAT SENT")
            sat_send_status=status[0]
        except Exception as error:
            # handle the exception
            print("Sending error", error)
        
sat_power_pin.value = False
#print("satellite sleeping")         

# send lora update
print("SENDING")
send_string=str(my_depth)+","+str(my_batt)+","+str(index)+","+str(sat_send_status)+","+str(attempt)
payload=bytes(send_string,"UTF-8")
led.value=True
send(base_node,payload)
led.value=False
    
rfm9x.sleep()

time.sleep(2) #for reading screen


#DONE pin
#done_pin = digitalio.DigitalInOut(board.D5)
done_pin = digitalio.DigitalInOut(board.A3)
done_pin.direction = digitalio.Direction.OUTPUT
done_pin.value=True



    
