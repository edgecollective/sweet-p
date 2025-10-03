import board
import busio
import digitalio
import time

uart = busio.UART(board.A4, board.D2, baudrate=9600)

depth_trigger = digitalio.DigitalInOut(board.D12)
depth_trigger.direction = digitalio.Direction.OUTPUT
depth_trigger.value=False

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


while True:

    depth_trigger.value=False
    time.sleep(1)
    print("trigger low")
    uart.reset_input_buffer()
    my_depth = get_depth()
    print("depth=",my_depth)
    
    time.sleep(1)
 
    depth_trigger.value=True
    time.sleep(1)
    print("trigger high")
    my_depth=-1
    my_depth = get_depth()
    print("my_depth=",my_depth)
    
    time.sleep(1)
   

