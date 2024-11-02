import board
import busio
import time
import digitalio


# ultrasonic uart
uart = busio.UART(board.A4,board.D2,baudrate=9600)
def get_depth():

    depth=-1
    
    for i in range(0,3):
    
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
    
while True:
    #hile True:
    data = uart.read(32)  # read up to 32 bytes
    # print(data)  # this is a bytearray type

    if data is not None:
        #ed.value = True

        # convert bytearray to string
        data_string = ''.join([chr(b) for b in data])
        print(data_string, end="")

        #ed.value = False
        
        #k
    #ata=uart_ultra.readline()
    #rint(data)
    else:
        print("None")
    time.sleep(1)

    
    
