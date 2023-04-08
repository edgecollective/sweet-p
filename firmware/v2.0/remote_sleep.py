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

node_id = 1


# Initialize one-wire bus on board pin D5.
ow_bus = OneWireBus(board.D5)

# set the time interval (seconds) for sending packets
transmit_interval = 600 

# Define radio parameters.
RADIO_FREQ_MHZ = 900.0  # Frequency of the radio in Mhz. Must match your
# module! Can be a value like 915.0, 433.0, etc.

# Define pins connected to the chip.
CS = digitalio.DigitalInOut(board.D6)
RESET = digitalio.DigitalInOut(board.D9)

# Initialize SPI bus.
spi = board.SPI()
# Initialze RFM radio
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)

# set node identity
rfm9x.node = node_id
# enable CRC checking
rfm9x.enable_crc = True
# set delay before sending ACK
rfm9x.ack_delay = 0.1
# set node addresses


def send(node_to,payload):
    rfm9x.destination = node_to
    if rfm9x.send_with_ack(payload):
        print("-->",node_to,payload)
        print("<--",node_to,"ACK")
    else:
        print("-->",node_to,payload)

def receive():
    packet = rfm9x.receive(with_ack=True, with_header=True)
    if packet is not None:
        node_from = packet[1]
        payload = "{0}".format(packet[4:])
        rssi = rfm9x.last_rssi
        #print("<--",node_from,"("+str(rssi)+")",payload)
        print("<--",node_from,"["+str(rssi)+"]",payload)
        return(packet)
    else:
        return(None)


print("Waiting for packets...")
time_now = time.monotonic()

#while True:
    #receive()
    # Scan for sensors and grab the first one found
    
#if time.monotonic() - time_now > transmit_interval:
    #time_now = time.monotonic()
try:
    sensor_list = ow_bus.scan()
    temps=str(node_id)+","
    for sensor in sensor_list:
        #print(sensor.rom)
        sensor_id=int(sensor.rom[2])
        #print("sensor_id:",sensor_id)
        #d=str(sensor.rom,"ascii")
        ds18 = DS18X20(ow_bus, sensor)
        this_temp="{0:0.3f}".format(ds18.temperature)
        time.sleep(1)
        temps=temps+str(sensor_id)+","+this_temp+","
        #print("Temperature: {0:0.3f}C".format(ds18.temperature))
    payload=bytes(temps,"UTF-8")
    print(payload)
    #payload = bytes("hello from node {}".format(rfm9x.node), "UTF-8")
    send(3,payload)
except Exception as e:
    print("error: ",e)

# Create a an alarm that will trigger 20 seconds from now.
time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + transmit_interval)
# Exit the program, and then deep sleep until the alarm wakes us.
alarm.exit_and_deep_sleep_until_alarms(time_alarm)
# Does not return, so we never get here.
