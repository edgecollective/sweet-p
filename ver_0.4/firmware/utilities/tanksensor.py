import board
import busio
import time
import digitalio



# ultrasonic uart
uart_ultra = busio.UART(board.A4, board.D2, baudrate=9600)

def get_depth():

    depth=-1
    
    for i in range(0,3):
    
        data=uart_ultra.readline()
        data_string = ''.join([chr(b) for b in data])
	print(data_string)
    
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

    #timestamp = get_timestamp()
    #print("ts=",timestamp)
    
    depth = get_depth()
    print("depth=",depth)
    
    time.sleep(1)
    
    print("----")
    
    
