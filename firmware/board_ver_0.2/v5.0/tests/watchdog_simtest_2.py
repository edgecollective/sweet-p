import time, board, digitalio, microcontroller, watchdog
w=microcontroller.watchdog; w.timeout=16; w.mode=watchdog.WatchDogMode.RESET
LED = digitalio.DigitalInOut(board.D13); LED.direction = digitalio.Direction.OUTPUT
a=0
w.deinit()

while True:
    #w.feed()
    for n in range(12):
        a=not a
        LED.value=a
        time.sleep(0.5)
    #time.sleep(15)
    print(b)
