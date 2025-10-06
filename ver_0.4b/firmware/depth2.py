import board
import busio
import digitalio

uart = busio.UART(board.A4, board.D2, baudrate=9600)


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
                
while True:
    
    data = readline_until("\r")
    if data is not None:
        print(data)
        print(data.split(" "))
        

