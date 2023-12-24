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
import adafruit_rfm9x


button_A_pin = digitalio.DigitalInOut(board.A5)
button_A_pin.direction = digitalio.Direction.INPUT

button_pressed=False

if(button_A_pin.value): #i.e. if button is pressed in our circuit, the value will be 'False'
    button_pressed=False
    print("button not pressed")
else:
    button_pressed=True
    print("button pressed!")

max_sat_send_attempts = 4

node_id = 2
base_node = 1
measure_interval_sec=2

# for the sd card

spi = board.SPI()
cs = board.D10

error_log = 1000000
SDCARD_ERROR = 1
DEPTH_ERROR = 10
CONNECT_ERROR = 100
SEND_ERROR = 1000
RTC_ERROR = 10000
MAX_TRIES_ERROR = 100000


# display on screen
display = board.DISPLAY
display.auto_refresh=False

font = bitmap_font.load_font("/Helvetica-Bold-16.bdf")
color_green = 0x00FF00
color_white = 0xFFFF
my_text="WATER SENSOR Ver 0.3\nGrass Nomads\n& Edge Collective"
my_text+="\n-----------------"
if (button_pressed):
    my_text+="\nForce Send: ON"
else:
    my_text+="\nForce Send: OFF"
text_area = label.Label(font, text=my_text, color=color_green)
text_area.x = 10
text_area.y = 20
display.show(text_area)
display.refresh()
time.sleep(1)


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
        #print("d=",d)
        if(len(d)==2):
            depth=int(d[0].strip('R'))
    
    return(depth)


def get_full_ts():
    t = rtc.datetime
    #ts = "{}/{}/{} {:02}".format(  # if we want to send every minute
    full_ts = "{}/{}/{} {:02}:{:02}".format(  # if we want to send every hour
        t.tm_mon,
        t.tm_mday,
        t.tm_year,
        t.tm_hour,
        t.tm_min
    )
    return(full_ts)


def get_timestamp():
    t = rtc.datetime
    ts = "{}/{}/{} {:02}".format(  # if we want to send every minute
    #ts = "{}/{}/{} {:02}".format(  # if we want to send every hour
        t.tm_mon,
        t.tm_mday,
        t.tm_year,
        t.tm_hour,
        t.tm_min
    )
    return(ts,int(t.tm_hour),int(t.tm_min))
    #return(ts,int(t.tm_hour))

temperature=-100
try:
    temperature=float(rtc.temperature)
except Exception as error:
    # handle the exception
    error_log = error_log+RTC_ERROR
    print("rtc error", error)

my_depth=-1
for i in range(0,10):
    if(my_depth<0):
        try:   
            my_depth = get_depth()
            print("depth=",my_depth)
        except Exception as error:
            # handle the exception
            print("depth sensor error", error)

if(my_depth<0):
    error_log = error_log+DEPTH_ERROR


should_send = False
send_result = 0

sd_ts=""
the_hour=-1
the_minute=-1
full_ts=""
try:
    sd_ts,the_hour,the_minute=get_timestamp()
    full_ts=get_full_ts()
    #sd_ts,the_hour=get_timestamp()
except Exception as error:
    # handle the exception
    error_log = error_log+RTC_ERROR
    print("rtc error", error)
    

print("last_date=",last_date)
print("sd_ts=",sd_ts)
print("the_hour=",the_hour)
print("the_minute=",the_minute)


the_hour_mst = the_hour-2
if(the_hour_mst < 0):
    the_hour_mst=the_hour_mst+24

the_time_mst="{:02}:{:02}".format(the_hour_mst,the_minute)

#text_area.text="Depth (cm): "+str(my_depth)+"\n\n"+str(full_ts)+" (EST)\nMST: "+str(the_hour_mst)+":"+str(the_minute)
text_area.text="Depth (cm): "+str(my_depth)+"\n\nTime: "+the_time_mst+" (MST)"
display.refresh()
time.sleep(10)

#print("the hour=",the_hour)

if (last_status==0):
    should_send = True
    text_area.text="Last send failed...\n...so send this time!"
    display.refresh()
    time.sleep(2)
    print("last send failed, so we should send this time!")
    
else:
    #if(the_minute>30):
    #if(the_hour%2==0):
    #my_hour=int(the_hour)
    # KEY LINE FOR DETERMINING WHEN TO SEND -- change this to the_hour_mst == 5 or the_hour_mst == 13
    #if(the_hour_mst==5 or the_hour_mst==13):
    if(the_hour%3==0):
        
        if(last_date!=sd_ts):
            should_send = True
            
            print("Right hour to send;\nhaven't sent this hour")
            
            text_area.text="Hour (MST): "+str(the_hour_mst)+"\n\nGood hour to send;\nhaven't sent this hour\n..so send!"
            display.refresh()
            time.sleep(4)
        else:
            print("Right hour to send;\nbut already sent this hour")
            text_area.text="Hour (MST): "+str(the_hour_mst)+"\n\nGood hour to send;\nbut already sent this hour\n..so don't send..."
            display.refresh()
            time.sleep(4)
    else:
        print("Not right hour to send.")
        text_area.text="Hour (MST): "+str(the_hour_mst)+"\n\nNot good hour to send..."
        display.refresh()
        time.sleep(4)
        
if (button_pressed):
    print("Force Send button pressed")
    print("... so, sending!")
    should_send=True
    text_area.text="\nForce Send Button pressed\n... so, sending!"
    display.refresh()
    time.sleep(4)
    

# in this radio code, we always get a ping when the device wakes up
# if the device thinks it should send, it sends a fake_depth of 1; else fake_depth = 0

if (should_send==True):
    fake_depth=1
else:
    fake_depth=0
    
# send radio ping that we woke up
# send radio and sleep
send_string=str(fake_depth)+","+str(temperature)
payload=bytes(send_string,"UTF-8")
#led.value=True
send(base_node,payload)
#led.value=False
rfm9x.sleep()


if (should_send==True):
#if True:

    print("recording a failure, until we succeed ...")
    # in case something freezes or we run out of time, first record a failure (send_result=0)
    record = sd_ts + "," + str(send_result)+"\n"
    try:
        with open("/sd/log.txt", "a") as f:
            #print("%d %0.1f %d\n" % (index,my_batt,my_depth))
            f.write(record)
            f.close()
    except Exception as error:
        # handle the exception
        error_log=error_log+SDCARD_ERROR
        print("sd card error", error)
        
    sat_send_status=32

    attempt=0
    max_num_sat_connect_attempts = 4
    connect_attempt = 0
    
    sat_power_pin = digitalio.DigitalInOut(board.A1)
    sat_power_pin.direction = digitalio.Direction.OUTPUT
    sat_power_pin.value = True
    print("satellite powered")
    text_area.x = 20
    text_area.y = 40
    text_area.text="Connecting to satellite..."
    display.refresh()
    time.sleep(3)
    
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
            data += struct.pack("f",temperature)
            data += struct.pack("i",error_log)
            
            #data += struct.pack("f",temperature)
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
            time.sleep(5)
            send_result = 1
            print("send_result=",send_result)
        else:
            text_area.text="Unable to send..."
            send_result = 0
            display.refresh()
            time.sleep(5)
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
        error_log=error_log+SDCARD_ERROR
        print("sd card error", error)

    

print("sleeping...")
text_area.text="Sleeping..."
display.refresh()
time.sleep(3)
#time.sleep(5)
        
# sleep
#print("sleeping ...")
done_pin = digitalio.DigitalInOut(board.A3)
done_pin.direction = digitalio.Direction.OUTPUT
done_pin.value=True
    
