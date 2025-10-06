import adafruit_sdcard
import busio
import digitalio
import board
import storage
import time

# Connect to the card and mount the filesystem.
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs = digitalio.DigitalInOut(board.D10)
sdcard = adafruit_sdcard.SDCard(spi, cs)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")

with open("/sd/test.txt", "r") as f:
    lines = f.readlines()
    print("numlines=",len(lines))
    
while True:

    # Use the filesystem as normal.
    with open("/sd/test.txt", "a") as f:
        f.write("Hello world\n")
    print("hello.")
    time.sleep(1)
