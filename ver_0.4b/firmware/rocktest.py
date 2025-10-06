import board
import time
uart=board.UART()
uart.baudrate=19200
from adafruit_rockblock import RockBlock
print("great")
time.sleep(1)
rb=RockBlock(uart)
time.sleep(2)
print(rb.model)
