# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
# Updated for Circuit Python 9.0
"""WiFi Simpletest"""

import os

import adafruit_connection_manager
import wifi

import adafruit_requests

import board
import busio
import digitalio
import time

uart_mesh = busio.UART(board.TX, board.RX, baudrate=115200, timeout=0)

# Get WiFi details, ensure these are setup in settings.toml
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
password = os.getenv("CIRCUITPY_WIFI_PASSWORD")
public_key=os.getenv("BAYOU_PUBLIC_KEY")
private_key=os.getenv("BAYOU_PRIVATE_KEY")


#public_key = "7pb4kprfp5cn"
#private_key = "ismxbyq54vbd"
base_url = "http://bayou.pvos.org/data/"
full_url = base_url+public_key

distance_meters=1.

TEXT_URL = "http://wifitest.adafruit.com/testwifi/index.html"
JSON_GET_URL = "https://httpbin.org/get"
JSON_POST_URL = base_url+public_key


# Initalize Wifi, Socket Pool, Request Session
pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
requests = adafruit_requests.Session(pool, ssl_context)
rssi = wifi.radio.ap_info.rssi


while True:

    data = uart_mesh.read(32)
    
    if data is not None:
       
        data_string = ''.join([chr(b) for b in data])
        #print("%r" % data_string)
        print(data_string)
        items = data_string.split(":")
        print(items)
        if len(items)==2:
            sensed=items[1].strip()
            print("sensed=",sensed)
            senseparse=sensed.split(",")
            depth=senseparse[0]
            battery=senseparse[1]
            
            print("depth=",depth)
            print("battery=",battery)
            
            print(f"\nConnecting to {ssid}...")
            print(f"Signal Strength: {rssi}")
            try:
                # Connect to the Wi-Fi network
                wifi.radio.connect(ssid, password)
            except OSError as e:
                print(f"❌ OSError: {e}")
            print("✅ Wifi!")


            json_data = {"private_key":private_key, "node_id":0,"distance_meters":depth,"battery_volts":battery}


            with requests.post(JSON_POST_URL, json=json_data) as response:
                resp = response.text
                print(resp)
            
            
                

