import ipaddress
import ssl
import wifi
import socketpool
import adafruit_requests
import time


# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

print("Connecting to %s"%secrets["ssid"])
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("Connected to %s!"%secrets["ssid"])

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

while True:
        
    ### posting data to bayou
    base_url = "http://bayou.pvos.org/data/"
    public_key = secrets["bayou_public"]
    private_key = secrets["bayou_private"]
    JSON_POST_URL = base_url+public_key

    node_id=0
    temp = 25.0

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
    #print("-" * 40)
    time.sleep(3)

