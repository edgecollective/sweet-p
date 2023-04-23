# Example to receive addressed packed with ACK and send a response
# Author: Jerry Needell
#
import time
import board
import busio
import digitalio
import adafruit_rfm9x
import ipaddress
import ssl
import wifi
import socketpool
import adafruit_requests

node_id = 3

# set the time interval (seconds) for sending packets
transmit_interval = 8

# Define radio parameters.
RADIO_FREQ_MHZ = 900.0  # Frequency of the radio in Mhz. Must match your
# module! Can be a value like 915.0, 433.0, etc.

# Define pins connected to the chip.
# set GPIO pins as necessary - this example is for Raspberry Pi
#CS = digitalio.DigitalInOut(board.D5)
#RESET = digitalio.DigitalInOut(board.D6)
CS = digitalio.DigitalInOut(board.D11)
RESET = digitalio.DigitalInOut(board.D6)

# Initialize SPI bus.
spi = board.SPI()
# Initialze RFM radio
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)

# reset the lora chip
rfm9x.reset()

# identity of this node
rfm9x.node = node_id
# enable CRC checking
rfm9x.enable_crc = True
# set delay before transmitting ACK (seconds)
rfm9x.ack_delay = 0.1
# set node addresses

# initialize counter
counter = 0
ack_failed_counter = 0

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

base_url = "http://bayou.pvos.org/data/"
public_key = secrets["bayou_public"]
private_key = secrets["bayou_private"]
JSON_POST_URL = base_url+public_key


print("Connecting to %s"%secrets["ssid"])
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("Connected to %s!"%secrets["ssid"])

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())


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
        #print("<--",node_from,"["+str(rssi)+"]",payload)
        #print
        return(packet)
    else:
        return(None)

print("Waiting for packets...")
#time_now = time.monotonic()

while True:
    packet = receive()
    if packet is not None:
        try:
            payload = "{0}".format(packet[4:])
            #print(payload)
            c=eval(str(payload,"ascii"))
            #print(c)
            d=str(c,"ascii")
            #decs=d.strip()
            decs=d.split(",")
            feed_id = int(decs.pop(0))
            N=2
            sensors = [decs[n:n+N] for n in range(0, len(decs), N)]
            #print(feed_id,sensors)
            for sensor in sensors:
                if len(sensor)==2:
                    sensorID=sensor[0]
                    node_id=0
                    temp=float(sensor[1])*9./5.+32.
                    print("RSSI:",rfm9x.last_rssi)
                    print(sensorID,temp)
                    if sensorID=='186':
                        node_id=1
                    #node_id=sensorID
                    json_data = {"private_key":private_key, "node_id":node_id,"temperature_c":temp}

                    # check wifi connect; connect if disconnected
                    if(wifi.radio.connect==False):
                        print("Connecting to %s"%secrets["ssid"])
                        wifi.radio.connect(secrets["ssid"], secrets["password"])
                        print("Connected to %s!"%secrets["ssid"])

                        pool = socketpool.SocketPool(wifi.radio)
                        requests = adafruit_requests.Session(pool, ssl.create_default_context())

                    # post data to bayou
                    print("Posting data...")
                    response = None
                    while not response:
                        try:
                            response = requests.post(JSON_POST_URL, json=json_data)
                            failure_count = 0
                            print(response.text)
                        except AssertionError as error:
                            print("Request failed, retrying...\n", error)
                            failure_count += 1
                            if failure_count >= attempts:
                                raise AssertionError(
                                    "Failed to resolve hostname, \
                                                    please check your router's DNS configuration."
                                ) from error
                            continue
        except:
            print("error")