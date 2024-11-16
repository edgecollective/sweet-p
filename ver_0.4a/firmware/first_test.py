import board
import busio
import digitalio
import displayio
import time
import adafruit_ds3231
import adafruit_sdcard
import storage
import terminalio
from adafruit_display_text import label
import adafruit_displayio_ssd1306
from analogio import AnalogIn

analog_in = AnalogIn(board.A1)

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

color_bitmap = displayio.Bitmap(128, 32, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0xFFFFFF  # White

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)

# Draw a smaller inner rectangle
inner_bitmap = displayio.Bitmap(118, 24, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000000  # Black
inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=5, y=4)
splash.append(inner_sprite)

# Draw a label
text = "Hello World!"
text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=28, y=15)
splash.append(text_area)


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
text_area.text="{}:{:02}:{:02}".format(t.tm_hour, t.tm_min, t.tm_sec)

the_hour=int(t.tm_hour)
the_minute=int(t.tm_min)

print("sd_ts=",sd_ts)
print("the_hour=",the_hour)

time.sleep(2)

########## setup sd card and get first line
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs = digitalio.DigitalInOut(board.D10)
try:
    sdcard = adafruit_sdcard.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")
    
    with open("/sd/test.txt", "r") as f:
        lines = f.readlines()
        last_line = lines[-1]
        print("last_line=",last_line)
        #print("numlines=",len(lines))
    
    #with open("/sd/test.txt", "a") as f:
        #f.write("Hello world\n")
        
    text_area.text="SD card works."
    
    
except Exception as error:
    print("sd card error", error)
    text_area.text="SD error"
    
time.sleep(1)

#######  try depth sensor
uart = busio.UART(board.A4, board.D2, baudrate=9600)

try:
    depth=get_depth()
    print("depth=",depth)
    text_area.text="depth = "+str(depth)+" cm"
    time.sleep(1)
except Exception as error:
    print("sd card error", error)
    text_area.text="depth error"

time.sleep(1)


#### try rtc
 

time.sleep(2)

########## try rockblock

rock_uart=board.UART()
rock_uart.baudrate=19200

try:
    from adafruit_rockblock import RockBlock
    rb=RockBlock(rock_uart)
    print(rb.model)
    text_area.text=rb.model
except Exception as error:
    print("rockblock error", error)
    text_area.text="rockblock error" 

#### try analog measurement

batt_factor=1.
batt_volts=get_voltage(analog_in)*batt_factor
batt_volts_str="{:.2f}".format(batt_volts)
text_area.text="batt(V)="+batt_volts_str
print("batt(V)="+batt_volts_str)

time.sleep(2)

    

