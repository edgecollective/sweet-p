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


    with open("/sd/freezer5.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            print(line)
    
except Exception as error:
    print("sd card error", error)
    text_area.text="SD card:\n"+error
   
time.sleep(2)

##############################

        

