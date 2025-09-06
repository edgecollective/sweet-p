import board
import busio
import digitalio
import time
from analogio import AnalogIn
import terminalio
import displayio

from adafruit_display_text import label
import adafruit_displayio_ssd1306

try:
    from i2cdisplaybus import I2CDisplayBus
except ImportError:
    from displayio import I2CDisplay as I2CDisplayBus
    
displayio.release_displays()
i2c = board.I2C()

i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
display_bus = I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

# Make the display context
splash = displayio.Group()
display.root_group = splash


# Draw a label

text="Pressure Test"

ta = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=5, y=5)
splash.append(ta)

time.sleep(2)

ta.text="starting..."

time.sleep(1)

analog_in = AnalogIn(board.A4)

while True:
    depth_v=(analog_in.value * 3.3) / 65536
    print(depth_v)
    ta.text=str(depth_v)
    time.sleep(1)


