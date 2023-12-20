import board
import busio
import time
import digitalio
import adafruit_ds3231
import sdcardio
import storage


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


# ultrasonic uart
uart_ultra = busio.UART(board.TX, board.RX, baudrate=9600)
trigger = digitalio.DigitalInOut(board.D5)
trigger.direction = digitalio.Direction.OUTPUT
trigger.value=False

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
    return(ts)


should_send = False
send_result = 0
    
if (last_status==0):
    should_send = True
    print("last send failed, so we should send this time!")
    
else:
    #if(nm_hour == 5 or nm_hour == 1):          
    #write every minute; otherwise can put above condition on write
    
    sd_ts=get_timestamp()
    
    print("last_date=",last_date)
    print("sd_ts=",sd_ts)
    
    if(last_date!=sd_ts):
        should_send = True
        print("new timestamp, so we should send this time!")
    else:
        print("same timestamp, shouldn't send")

if (should_send):

    depth = get_depth()
    print("depth=",depth)
    
    print("SENDING")
    send_result = 1 # assume this for now; update from satellite code
    
    
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

   
    
