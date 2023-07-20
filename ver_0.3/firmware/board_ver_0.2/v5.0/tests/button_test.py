# SPDX-FileCopyrightText: 2019 Dave Astels for Adafruit Industries
# SPDX-License-Identifier: MIT

# pylint: disable=invalid-name

import board
import digitalio
from adafruit_debouncer import Debouncer
import time

pin = digitalio.DigitalInOut(board.A0)
pin.direction = digitalio.Direction.INPUT
pin.pull = digitalio.Pull.UP
switch = Debouncer(pin)

while True:
    switch.update()
    if switch.fell:
        print("Pressed!")
        time.sleep(2)

    #if switch.rose:
    #    print("Just released")
    #if switch.value:
    #    print("not pressed")
    #else:
    #    print("pressed")