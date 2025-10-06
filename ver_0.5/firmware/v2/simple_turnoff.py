import time
import board
import adafruit_ds3231
import busio
import digitalio


# the control pin
latch=digitalio.DigitalInOut(board.P0_09)
latch.direction=digitalio.Direction.OUTPUT
latch.value=False

led=digitalio.DigitalInOut(board.LED)
led.direction=digitalio.Direction.OUTPUT
led.value=False

# Main loop to check for alarms
while True:
    
    for i in range(0,5):
        led.value=True
        time.sleep(1)
        led.value=False
        time.sleep(1)

    #blink to indicate latch pull    
    led.value=True
    time.sleep(.1)
    led.value=False
    time.sleep(.1)
    
    latch.value=True
    time.sleep(.1)
    latch.value=False
    
