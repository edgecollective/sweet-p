import board
import busio
import sdcardio
import storage
import digitalio
import microcontroller
import time
import math

led = digitalio.DigitalInOut(board.D13)
led.direction = digitalio.Direction.OUTPUT

#spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
spi = board.SPI()
#spi = busio.SPI(clock=board.GP10, MOSI=board.GP11, MISO=board.GP12)

#cs = digitalio.DigitalInOut(board.GP2)
cs = board.D10
sdcard = sdcardio.SDCard(spi, cs)
vfs = storage.VfsFat(sdcard)

storage.mount(vfs, "/sd")

send_count = 5

index = -1

with open("/sd/log.txt", "r") as f:
    lines = f.readlines()
    print("Printing lines in file:")
    #for line in lines:
    #    print(line)
    last_line = lines[-1]
    j = last_line.split(' ')[0]
    print("last line:")
    print(lines[-1])
    print("j:")
    print(j)

index = int(j)
      
while True:

    index=index+1
    
    with open("/sd/log.txt", "a") as f:
        led.value = True  # turn on LED to indicate we're writing to the file
        t = microcontroller.cpu.temperature
        print("%d %0.1f\n" % (index,t))
        f.write("%d %0.1f\n" % (index,t))
        led.value = False  # turn off LED to indicate we're done
    # file is saved
    
    if(index%send_count==0):
        print("SEND")
    time.sleep(1)

    #with open("/sd/test.txt", "r") as f:
    #    print("Read line from file:")
    #    print(f.readline())
