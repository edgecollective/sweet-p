import board
import busio
import time
import digitalio
import adafruit_ds3231
import sdcardio
import storage
import adafruit_rfm9x
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import analogio


# for the sd card
spi = board.SPI()
cs = board.D10

#LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT


node_id=2
base_node=1


error_log = 100000
SDCARD_ERROR = 1
DEPTH_ERROR = 10
CONNECT_ERROR = 100
SEND_ERROR = 1000
MAX_TRIES_ERROR = 10000

# radio params
RADIO_FREQ_MHZ = 900.0
LORA_CS = digitalio.DigitalInOut(board.D6)
LORA_RESET = digitalio.DigitalInOut(board.D9)

rfm9x = adafruit_rfm9x.RFM9x(spi, LORA_CS, LORA_RESET, RADIO_FREQ_MHZ)
rfm9x.node = node_id
rfm9x.enable_crc = True
rfm9x.ack_delay = .1
print("LoRa OK")


# for the RTC
i2c = board.I2C()  # uses board.SCL and board.SDA
rtc = adafruit_ds3231.DS3231(i2c)
days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

ads = ADS.ADS1115(i2c)
chan = AnalogIn(ads, ADS.P0)


# ultrasonic uart
uart_ultra = busio.UART(board.TX, board.RX, baudrate=9600)
trigger = digitalio.DigitalInOut(board.D5)
trigger.direction = digitalio.Direction.OUTPUT
trigger.value=False

def send(node_to,payload):
    rfm9x.destination = node_to
    #if rfm9x.send_with_ack(payload):
    #    print("-->",node_to,payload)
    #    print("<--",node_to,"ACK")
    #else:
    #    print("-->",node_to,payload)
    rfm9x.send(payload)
    print("-->",node_to,payload)


def get_depth():

    depth=-1
    
    for i in range(0,3):
    
        trigger.value=False
        time.sleep(1)
        trigger.value=True
        time.sleep(.01)
        trigger.value=False
        data=uart_ultra.readline()
        data_string = ''.join([chr(b) for b in data])
        d=data_string.split(' ')
        if(len(d)==2):
            depth=int(d[0].strip('R'))
    
    return(depth)

def get_timestamp():
    t = rtc.datetime
    ts = "{}/{}/{} {:02}:{:02}".format(
        t.tm_mon,
        t.tm_mday,
        t.tm_year,
        t.tm_hour,
        t.tm_min
    )
    return(ts,int(t.tm_min))

# mount the sd card
try:
    sdcard = sdcardio.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")
except Exception as error:
    # handle the exception
    error_log = error_log+SDCARD_ERROR
    print("sd card error:", error)
        
        
while True:

    print("------------------------")
    should_send = False
    send_result = 0
        
    sd_ts,minute=get_timestamp()

    # mount the sd card and get the last line
    try:
        with open("/sd/log.txt", "r") as f:
            lines = f.readlines()
            last_line = lines[-1].strip().split(",")
            last_date=last_line[0].strip()
            last_status=int(last_line[1].strip())
        f.close()
    except Exception as error:
        # handle the exception
        error_log = error_log+SDCARD_ERROR
        print("sd card error:", error)

    print("last_line=",last_line)
    print("sd_ts=",sd_ts)

    if (last_status==0):
        should_send = True
        print("last send failed, so we should send this time!")
        
    else:
        print("minute=",minute)
        print("minute%2=",minute%2)
        if(minute%2==0):
            print("it's a proper minute!")
        #if(nm_hour == 5 or nm_hour == 1):          
        #write every minute; otherwise can put above condition on write   
            print("last_date=",last_date)
            print("sd_ts=",sd_ts)
            
            if(last_date!=sd_ts):
                should_send = True
                print("... and new timestamp, so we should send this time!")
            else:
                print("... but same timestamp, shouldn't send")


    depth = get_depth()
    print("depth=",depth)

    battery_voltage = chan.voltage*2 #voltage divider
    my_batt=battery_voltage
    print("my_batt=",battery_voltage)

    temperature=rtc.temperature


    if (should_send):

        print("SENDING VIA SATELLITE")
        
        send_result = 1 # assume this for now; update from satellite code
        
        
        print("recording date & success")
                
        record = sd_ts + "," + str(send_result)+"\n"

        print("record=",record)
        try:
            with open("/sd/log.txt", "a") as f:
                #print("%d %0.1f %d\n" % (index,my_batt,my_depth))
                f.write(record)
                f.close()
        except Exception as error:
            # handle the exception
            error_log=error_log+SDCARD_ERROR
            print("sd card error", error)

        print('sending via radio')
        send_string=str(depth)+","+str(temperature)
        payload=bytes(send_string,"UTF-8")
        led.value=True
        send(base_node,payload)
        led.value=False
            
        rfm9x.sleep()
        
        print("sleeping...")
        time.sleep(5)
    

    
