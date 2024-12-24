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

temperature=-99
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
            #print(data)
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


depth=-1

text_area.text="Reading depth\nsensor..."


while True:

    try:
        depth=get_depth()
        print("depth=",depth)
        if (depth==-1):
            text_area.text="No depth sensor?\nCheck connection!\n\nSending depth=-1 cm"
        else:
            text_area.text="Depth = "+str(depth)+" cm"
        
    except Exception as error:
        print("depth sensor error", error)
        text_area.text="depth error\n"+error

    time.sleep(1)


        

