import time
import board
import analogio

analog_pin = analogio.AnalogIn(board.A0)

while True:

    raw_value = analog_pin.value
    print(raw_value)
    time.sleep(1)
