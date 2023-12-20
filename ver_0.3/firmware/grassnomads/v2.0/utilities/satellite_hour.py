import board
import busio
import time
import digitalio
import adafruit_ds3231
import sdcardio
import storage
import analogio
import struct
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import displayio
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import label
from adafruit_rockblock import RockBlock

max_sat_send_attempts = 20

node_id = 2
base_node = 1
measure_interval_sec=2

# for the sd card

spi = board.SPI()
cs = board.D10

# mount the sd card and get the last line
try:
    sdcard = sdcardio.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")
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


# for the RTC
i2c = board.I2C()  # uses board.SCL and board.SDA
rtc = adafruit_ds3231.DS3231(i2c)
days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

# ADS
ads = ADS.ADS1115(i2c)
chan = AnalogIn(ads, ADS.P0)
battery_voltage = chan.voltage*2 #voltage divider
my_batt=battery_voltage

# ultrasonic uart
uart_ultra = busio.UART(board.TX, board.RX, baudrate=9600)
trigger = digitalio.DigitalInOut(board.D5)
trigger.direction = digitalio.Direction.OUTPUT
trigger.value=False


# display on screen
display = board.DISPLAY
display.auto_refresh=False

font = bitmap_font.load_font("/Helvetica-Bold-16.bdf")
color_green = 0x00FF00
color_white = 0xFFFF
my_text="WATER LEVEL SENSOR\nVersion 0.3\n------------------------\nGrass Nomads\n& Edge Collective"
text_area = label.Label(font, text=my_text, color=color_green)
text_area.x = 10
text_area.y = 20
display.show(text_area)
display.refresh()
#time.sleep(1)

error_log = 100000
SDCARD_ERROR = 1
DEPTH_ERROR = 10
CONNECT_ERROR = 100
SEND_ERROR = 1000
MAX_TRIES_ERROR = 10000



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
    #ts = "{}/{}/{} {:02}:{:02}".format(  # if we want to send every minute
    ts = "{}/{}/{} {:02}".format(  # if we want to send every hour
        t.tm_mon,
        t.tm_mday,
        t.tm_year,
        t.tm_hour,
        t.tm_min
    )
    return(ts,int(t.tm_hour))


should_send = False
send_result = 0

sd_ts,the_hour=get_timestamp()

print("sd_ts=",sd_ts)
print("the_hour=",the_hour)

if (last_status==0):
    should_send = True
    print("last send failed, so we should send this time!")
    
else:
    print("the_hour=",the_hour)
    if(the_hour == 1 or the_hour == 5 or the_hour == 10 or the_hour == 13 or the_hour == 18 or the_hour == 22):
        print("last_date=",last_date)
        print("sd_ts=",sd_ts)
        
        if(last_date!=sd_ts):
            should_send = True
            print("new timestamp, so we should send this time!")
        else:
            print("same timestamp, shouldn't send")

if (should_send==True):

    my_depth=-1
    try:   
        my_depth = get_depth()
        print("depth=",my_depth)
    except Exception as error:
        # handle the exception
        error_log = error_log+DEPTH_ERROR
        print("depth sensor error", error)
        
    sat_send_status=32

    attempt=0
    max_num_sat_connect_attempts = 4
    connect_attempt = 0
    
    sat_power_pin = digitalio.DigitalInOut(board.A1)
    sat_power_pin.direction = digitalio.Direction.OUTPUT
    sat_power_pin.value = True
    print("satellite powered")
    text_area.text="Connecting to satellite..."
    display.refresh()
    #time.sleep(3)
    
    sat_connect_success=False
    uart = busio.UART(board.D12, board.D11, baudrate=19200)
    
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
            error_log = error_log+CONNECT_ERROR
            print("Connecting error:", error)
        
        connect_attempt=connect_attempt+1
        
        
    if(sat_connect_success==True):
        try:
            
            data = struct.pack("f",my_batt)
            data += struct.pack("i",my_depth)
            data += struct.pack("i",attempt)
            rb.data_out = data
  
            print("Talking to satellite...")
            
            attempt=attempt+1
            status=rb.satellite_transfer()
            print(attempt,status)
            text_area.x = 20
            text_area.y = 40
            text_area.text="Connecting to satellite...\nSend attempt # "+str(attempt)+" of "+str(max_sat_send_attempts)+"\nStatus:"+str(status)
            display.refresh()
            
            while status[0] > 4 and attempt<max_sat_send_attempts:
                attempt=attempt+1
                #time.sleep(10)
                #print(attempt, status)
                status=rb.satellite_transfer()
                print(attempt, status)
                text_area.text="Connecting to satellite...\nSend attempt # "+str(attempt)+" of "+str(max_sat_send_attempts)+"\nStatus:"+str(status)
                display.refresh()
                
                #text_area.text=str(status)+"\nattempt "+str(attempt)
                time.sleep(1)
                
            #print("SAT SENT")
            sat_send_status=status[0]
        except Exception as error:
            # handle the exception
            error_log = error_log+SEND_ERROR
            print("Sending error", error)
            
        if(sat_send_status<=4): # successful satellite connection; increment index
            text_area.text="SENT!"
            display.refresh()
            send_result = 1
        else:
            text_area.text="Unable to send..."
            #send_result = 0
            display.refresh()
            error_log = error_log+MAX_TRIES_ERROR
       

print("recording date & success")
    
record = sd_ts + "," + str(send_result)+"\n"

try:
    with open("/sd/log.txt", "a") as f:
        #print("%d %0.1f %d\n" % (index,my_batt,my_depth))
        f.write(record)
        f.close()
except Exception as error:
    # handle the exception
    error_log=error_log++SDCARD_ERROR
    print("sd card error", error)

time.sleep(2)

# sleep
print("sleeping ...")
done_pin = digitalio.DigitalInOut(board.A3)
done_pin.direction = digitalio.Direction.OUTPUT
done_pin.value=True
    
