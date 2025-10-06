import board
import busio
import time
import digitalio
import sdcardio
import storage
import struct
import adafruit_ds3231

print("hello")

spi = board.SPI()
cs = board.D10

error_log = 1000000
SDCARD_ERROR = 1
DEPTH_ERROR = 10
CONNECT_ERROR = 100
SEND_ERROR = 1000
RTC_ERROR = 10000
MAX_TRIES_ERROR = 100000

# for the RTC
i2c = board.I2C()  # uses board.SCL and board.SDA
rtc = adafruit_ds3231.DS3231(i2c)
days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

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


should_send = False
send_result = 0

sd_ts=""
the_hour=-1
the_minute=-1
full_ts=""

try:
    sd_ts,the_hour,the_minute=get_timestamp()
    full_ts=get_full_ts()
except Exception as error:
    # handle the exception
    error_log = error_log+RTC_ERROR
    print("rtc error", error)

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
    
    
try:
    sdcard = sdcardio.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")
    with open("/sd/log.txt", "r") as f:
        lines = f.readlines()
        last_line = lines[-1].strip().split(",")
        print("last_line=",last_line)
        last_date=last_line[0].strip()
        last_status=int(last_line[1].strip())
    f.close()
except Exception as error:
    # handle the exception
    error_log = error_log+SDCARD_ERROR
    print("sd card error:", error)

