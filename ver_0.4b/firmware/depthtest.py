import board
import busio
import digitalio
import time

uart = busio.UART(board.A4, board.D2, baudrate=9600)

def get_depth():

    depth=-1
    
    for i in range(0,3):
    
        #trigger.value=False
        time.sleep(1)
        #trigger.value=True
        time.sleep(.01)
        #trigger.value=False
        data=uart.readline()
        data_string = ''.join([chr(b) for b in data])
        d=data_string.split(' ')
        #print("d=",d)
        if(len(d)==2):
            depth=int(d[0].strip('R'))
    
    return(depth)

while True:

    my_depth=-1
    for i in range(0,10):
        if(my_depth<0):
            try:   
                my_depth = get_depth()
                print("depth=",my_depth)
            except Exception as error:
                print("depth error",error)
    time.sleep(1)
   

