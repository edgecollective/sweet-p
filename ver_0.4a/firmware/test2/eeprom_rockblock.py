import board
import struct
import adafruit_24lc32
import adafruit_ds3231
import time

import displayio

uart = board.UART()
uart.baudrate = 19200

from adafruit_rockblock import RockBlock

rb = RockBlock(uart)

wakeup_times = [15, 30, 45]  #these are the minutes to wake up

wakeup_stats = [0, 0, 0] #these record the last minute that each item was sent

MAX_RETRY = 5
SLEEP_BETWEEN = 10

# Compatibility with both CircuitPython 8.x.x and 9.x.x.
# Remove after 8.x.x is no longer a supported release.
try:
    from i2cdisplaybus import I2CDisplayBus
except ImportError:
    from displayio import I2CDisplay as I2CDisplayBus

import terminalio
from adafruit_display_text import label
import adafruit_displayio_ssd1306

displayio.release_displays()
    
# Initialize I2C and EEPROM
i2c = board.I2C()

display_bus = I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

# Make the display context
splash = displayio.Group()
display.root_group = splash


text="Starting up..."

wakeup_times_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=5, y=5)
splash.append(wakeup_times_area)
wakeup_times_area.text="wakeup: "+' '.join(str(item) for item in wakeup_times)

wakeup_stats_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=5, y=15)
splash.append(wakeup_stats_area)
wakeup_stats_area.text="stats: "+' '.join(str(item) for item in wakeup_stats)

current_time_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=5, y=25)
splash.append(current_time_area)

# eeprom
eeprom = adafruit_24lc32.EEPROM_I2C(i2c, address=0x57)

#rtc

rtc = adafruit_ds3231.DS3231(i2c)

# 4 integers to write to EEPROM
#wakeup_stats = [5, 13, 18, 25]  #hour1, hour2, hour3, day of month

days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def write_to_eeprom(integers_to_write):
    # Convert integers to bytes and write to EEPROM
    # Each integer takes 4 bytes, so we'll use addresses 0, 4, 8, 12
    print("Writing integers to EEPROM...")
    print(f"Original integers: {integers_to_write}")
    
    for i, value in enumerate(integers_to_write):
        # Pack integer as 4-byte signed integer (little-endian)
        byte_data = struct.pack('<i', value)
        start_addr = i * 4
        
        # Write the 4 bytes to EEPROM
        for j, byte in enumerate(byte_data):
            eeprom[start_addr + j] = byte
        
        print(f"Wrote integer {value} to EEPROM at address {start_addr}")
    
def read_from_eeprom():
    print("\nReading integers from EEPROM...")

    # Read back the integers
    retrieved_integers = []
    for i in range(3):
        start_addr = i * 4
        
        # Read 4 bytes from EEPROM as a slice (returns bytearray)
        byte_data = eeprom[start_addr:start_addr + 4]
        
        # Unpack bytes back to integer
        retrieved_value = struct.unpack('<i', byte_data)[0]
        retrieved_integers.append(retrieved_value)
        
        print(f"Read integer {retrieved_value} from EEPROM at address {start_addr}")
    
    return(retrieved_integers)

# wakup and check the time


t = rtc.datetime

print(
        "The date is {} {}/{}/{}".format(
            days[int(t.tm_wday)], t.tm_mday, t.tm_mon, t.tm_year
        )
    )
print("The time is {}:{:02}:{:02}".format(t.tm_hour, t.tm_min, t.tm_sec))

print("the minute is {:02}".format(t.tm_min))

print("the hour is {:02}".format(t.tm_hour))

#write_to_eeprom([0,0,0])

#stats = read_from_eeprom()

t = rtc.datetime

print("---------------------------------")
print("wakeup_times=",wakeup_times)

print("the hour is {:02}".format(t.tm_hour))

print("the minute is {:02}".format(t.tm_min))

stats = read_from_eeprom()



t = rtc.datetime
current_time_area.text="hr:{:02} min:{:02} sec:{:02}".format(t.tm_hour,t.tm_min,t.tm_sec)
wakeup_stats_area.text="stats: "+' '.join(str(item) for item in stats)

print(current_time_area.text)

latest_send_time_index=-1

for i in range(len(wakeup_times)-1):
    this_minute=wakeup_times[i]
    if (this_minute<=t.tm_min):
        latest_send_time_index=i

print("latest_send_time_index=",latest_send_time_index)

if(latest_send_time_index>-1): #then we've gotten to a time to send, or blown past it
    
    #turn on satellite
    
    #send
    rb.text_out = "hello world"

    # try a satellite Short Burst Data transfer
    print("Talking to satellite...")
    status = rb.satellite_transfer()
    # loop as needed
    retry = 0
    while status[0] > 8 and retry<MAX_RETRY:
        status = rb.satellite_transfer()
        print(retry, status)
        retry += 1
        time.sleep(SLEEP_BETWEEN)

    if (status[0] <= 8):
        print("SENT")
        #update the stats
        for i in range(latest_time_index+1):
            stats[i]=t.tm_hour
        write_to_eeprom(stats)
    else:
        print("DIDN'T SEND")
    
    #mark this time and all previous for the hour as 'sent'
    # turn off satellite





    


