import board
import busio
import digitalio
import displayio
import time
import adafruit_ds3231
import adafruit_sdcard
import storage
import struct
import terminalio
from adafruit_display_text import label
import adafruit_displayio_ssd1306
from analogio import AnalogIn
from adafruit_rockblock import RockBlock

analog_in = AnalogIn(board.A1)

sat_power_pin = digitalio.DigitalInOut(board.D9)
sat_power_pin.direction = digitalio.Direction.OUTPUT
sat_power_pin.value = False

button_A_pin = digitalio.DigitalInOut(board.A5)
button_A_pin.direction = digitalio.Direction.INPUT
button_pressed=False

led = digitalio.DigitalInOut(board.D13)
led.direction = digitalio.Direction.OUTPUT
led.value=False

depth_trigger = digitalio.DigitalInOut(board.D12)
depth_trigger.direction = digitalio.Direction.OUTPUT
depth_trigger.value=False

depth=-1  #default value

if(button_A_pin.value): #i.e. if button is pressed in our circuit, the value will be 'False'
    button_pressed=False
    print("button not pressed")
else:
    button_pressed=True
    print("button pressed!")
    led.value=True


send_result = 0 
should_send = False
max_num_sat_connect_attempts = 4
max_sat_send_attempts = 4

temperature=-100
error_log = 1000000
SDCARD_ERROR = 1
DEPTH_ERROR = 10
CONNECT_ERROR = 100
SEND_ERROR = 1000
RTC_ERROR = 10000
MAX_TRIES_ERROR = 100000

time.sleep(1)

# set up ultrasonic uart early on
uart = busio.UART(board.A4, board.D2, baudrate=9600)

def get_voltage(pin):
    return (pin.value * 3.3) / 65536
    

def readline_until(end_char):
    line = ""
    while True:
        char = uart.read(1)
        if char:
            char = char.decode()
            if char == end_char:
                return line
            else:
                line += char
        else:
            return line
                
def get_depth():

    depth=-1
    for i in range(0,5):
        print("i=",i)
        data = readline_until("\r")
        if data is not None:
            print(data)
            depth_data=data.split(" ")
            if len(depth_data)==2:
                d1=depth_data[0]
                if (d1[0]=='R'):
                    depth=int(d1[1:])
    return(depth)

def get_timestamp():
    t = rtc.datetime
    ts = "{}/{}/{} {:02}".format(  # if we want to send every minute
        t.tm_mon,
        t.tm_mday,
        t.tm_year,
        t.tm_hour,
        t.tm_min
    )
    return(ts,int(t.tm_hour),int(t.tm_min))
    
##### setup display
try:
    from i2cdisplaybus import I2CDisplayBus
except ImportError:
    from displayio import I2CDisplay as I2CDisplayBus

displayio.release_displays()

i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
display_bus = I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

# Make the display context
splash = displayio.Group()
display.root_group = splash


# Draw a label

text="Starting up..."
if(button_pressed):
    text = "Starting up...\n\nButton pressed:\nForce send!"
text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=5, y=5)
splash.append(text_area)
time.sleep(2)


# try battery measurement      
        
batt_factor=5.*1.15
batt_volts=get_voltage(analog_in)*batt_factor
batt_volts_str="{:.2f}".format(batt_volts)
text_area.text="Battery:\n"+batt_volts_str + " Volts"
print("batt(V)="+batt_volts_str)

time.sleep(2)

## rtc

rtc = adafruit_ds3231.DS3231(i2c)
days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

if False:  # change to True if you want to set the time!
    #                     year, mon, date, hour, min, sec, wday, yday, isdst
    t = time.struct_time((2024, 11, 12, 21, 21, 15, 0, -1, -1))
    print("Setting time to:", t)  # uncomment for debugging
    rtc.datetime = t
    print()
    
t = rtc.datetime
print("initial_rtc=",t.tm_hour,t.tm_min,t.tm_sec)
text_area.text="Time (EST):\n{}:{:02}:{:02}".format(t.tm_hour, t.tm_min, t.tm_sec)

sd_ts=""
the_hour=-1
the_minute=-1
full_ts=""

the_hour=int(t.tm_hour)
the_minute=int(t.tm_min)


try:
    sd_ts,the_hour,the_minute=get_timestamp()
    #full_ts=get_full_ts()
    #sd_ts,the_hour=get_timestamp()
except Exception as error:
    # handle the exception
    error_log = error_log+RTC_ERROR
    print("rtc error", error)

print("sd_ts=",sd_ts)
print("the_hour=",the_hour)
print("the_hour=",the_hour)
print("the_minute=",the_minute)

the_hour_mst = the_hour-2
if(the_hour_mst < 0):
    the_hour_mst=the_hour_mst+24

the_time_mst="{:02}:{:02}".format(the_hour_mst,the_minute)

print("the_time_mst=",the_time_mst)

time.sleep(2)

########## setup sd card and get last line
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs = digitalio.DigitalInOut(board.D10)

try:
    sdcard = adafruit_sdcard.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")


    if False: # set this to True to write some example data to the sd card
        print("creating good sd card data")
        record = sd_ts + "," + str(send_result)+ "," + str(depth)+"\n"
        with open("/sd/log.txt", "a") as f:
            #print("%d %0.1f %d\n" % (index,my_batt,my_depth))
            f.write(record)
            f.close()


    with open("/sd/log.txt", "r") as f:
        lines = f.readlines()
        last_line = lines[-1].strip().split(",")
        print("last_line=",last_line)
        last_date=last_line[0].strip()
        last_status=int(last_line[1].strip())
        last_depth=int(last_line[2].strip())
        print("last_line=",last_line)
        print("last_date=",last_date)
        print("last_status=",last_status)
        print("last_depth=",last_depth)
        #last_line = lines[-1]
        #print("last_line=",last_line)
        #print("numlines=",len(lines))

    #with open("/sd/test.txt", "a") as f:
        #f.write("Hello world\n")
        
    text_area.text="SD card:\ngood."
    
except Exception as error:
    print("sd card error", error)
    text_area.text="SD card:\n"+error
   
time.sleep(2)

##############################

# okay, now we have the current date, and the last date and status

# quick get the depth and the battery level

#######  try depth sensor

text_area.text="Reading depth\nsensor..."

try:

    depth_trigger.value=False
    time.sleep(1)
    print("trigger low")
    uart.reset_input_buffer()
    depth = get_depth()
    print("depth=",depth)
    
    time.sleep(1)
 
    depth_trigger.value=True
    time.sleep(1)
    print("trigger high")
    depth=-1
    depth = get_depth()
    print("my_depth=",depth)
    
    
    if (depth==-1):
        text_area.text="No depth sensor?\nCheck connection!\n\nSending depth=-1 cm"
    else:
        text_area.text="Depth = "+str(depth)+" cm"
    
    time.sleep(1)
except Exception as error:
    print("depth sensor error", error)
    text_area.text="depth error\n"+error

time.sleep(2)

######## try temperature  

text_area.text="Getting temp\nfrom RTC..."

temperature=-100
try:
    temperature=float(rtc.temperature)
    text_area.text="Temp="+str(temperature)+"C"
except Exception as error:
    # handle the exception
    error_log = error_log+RTC_ERROR
    print("rtc error", error)
    text_area.text="RTC temp error"

time.sleep(2)

## now assess whether to send via satellite


#always send if button pressed
if (button_pressed): 
    print("Force Send button pressed")
    print("... so, sending!")
    should_send=True
    text_area.text="\nForce Send button\npressed: sending!"
    display.refresh()
    time.sleep(2)
    
# if we tried to send last time and couldn't, then send this time
elif (last_status==0):
    should_send = True
    text_area.text="Last send failed...\n...so send this time!"
    display.refresh()
    time.sleep(2)
    print("last send failed, so we should send this time!")


# if the last reading recorded was 999, but this one isn't, then send the new reading
# note: a 999 only would've been recorded if a send was attempted
elif (last_depth==999 or last_depth==-1) and (depth!=999) and (depth!=-1):
    should_send=True
    print("got sensor=999 before;\n now send good value")
        
    text_area.text="got sensor=999 before;\n now send good value"
    display.refresh()
    time.sleep(2)
    
# if it's the proper time to send, then send
elif (the_hour_mst==5 or the_hour_mst==13):
#elif (the_hour_mst%3==0): # send every 1 hours
    if (last_date!=sd_ts): # if we haven't already sent this hour
    
        should_send=True
        print("Right hour to send;\nhaven't sent this hour")
        
        text_area.text="Hour (MST): "+str(the_hour_mst)+"\n\nGood hour to send;\nhaven't sent this hour\n..so send!"
        display.refresh()
        time.sleep(2)
            
    else:
        print("Not right hour to send.")
        text_area.text="Hour (MST): "+str(the_hour_mst)+"\n\nNot good hour to send..."
        display.refresh()
        time.sleep(4)
    


if (should_send==True):

    ## if should send, collect data and try to send

    ## first record a failure in case something freezes / we run out of time

    print("recording a failure, until we succeed ...")
        # in case something freezes or we run out of time, first record a failure (send_result=0)
    record = sd_ts + "," + str(send_result)+ "," + str(depth)+"\n"
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
    connect_attempt = 0
    
    ## power up the satellite
    sat_power_pin.value = True
    print("satellite powered")
    #text_area.x = 20
    #text_area.y = 40
    text_area.text="Connecting to\nsatellite..."
    display.refresh()
    time.sleep(3)
    sat_connect_success=False
    
    rock_uart=board.UART()
    rock_uart.baudrate=19200

    while (connect_attempt < max_num_sat_connect_attempts) and (sat_connect_success==False):
        try:
            rb=RockBlock(rock_uart)
            print(rb.model)
            text_area.text=rb.model
            sat_connect_success=True
            
        except Exception as error:
            print("Satellite error", error)
            text_area.text="Satellite error" 
    
        connect_attempt=connect_attempt+1

    if(sat_connect_success==True):
        print("then we connect to satellite")
        text_area.text="Preparing satellite\ndata..."
        time.sleep(1)
        
        #try:
        data = struct.pack("f",batt_volts)
        data += struct.pack("i",depth)
        data += struct.pack("i",attempt)
        data += struct.pack("f",temperature)
        data += struct.pack("i",error_log)
    
        rb.data_out = data
    
        print("Talking to satellite...")
        
        attempt=attempt+1
        status=rb.satellite_transfer()
        print(attempt,status)
        
        #text_area.x = 20
        #text_area.y = 40
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
        #except Exception as error:
            # handle the exception
        #    error_log = error_log+SEND_ERROR
        #    print("Sending error", error)
            
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
    record = sd_ts + "," + str(send_result)+ "," + str(depth)+"\n"

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
done_pin = digitalio.DigitalInOut(board.D7)
done_pin.direction = digitalio.Direction.OUTPUT
done_pin.value=True 
        

