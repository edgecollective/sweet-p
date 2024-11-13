#from adafruit_debouncer import Debouncer
import digitalio
import board
from digitalio import DigitalInOut, Direction, Pull
import time


button_A_pin = digitalio.DigitalInOut(board.A5)
button_A_pin.direction = digitalio.Direction.INPUT


#button_A_pin.pull = digitalio.Pull.UP
#button_A = Debouncer(button_A_pin)


while True:

    print(button_A_pin.value)
    time.sleep(1)
