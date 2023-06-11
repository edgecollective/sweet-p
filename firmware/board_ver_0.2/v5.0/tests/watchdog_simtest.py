from microcontroller import watchdog
from watchdog import WatchDogMode
from time import sleep

wdt = watchdog
wdt.timeout = 10
wdt.mode = WatchDogMode.RESET

counter = 0
while True:
    counter += 1
    if counter >= 5:
        raise Exception("Simulated Error.")
    print(counter)
    sleep(1)
