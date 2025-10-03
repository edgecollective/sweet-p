
import time
import board
import digitalio
import microcontroller

led = digitalio.DigitalInOut(board.LED)
led.switch_to_output()


#with open("/temperature.txt", "r") as f:
#    lines = f.readlines()
#    last_line=lines[-1]
#    print(last_line)

index=0

try:
    with open("/temperature.txt", "a") as datalog:
        while True:
            #temp = microcontroller.cpu.temperature
            #status=0
            #depth=2
            datalog.write(str(index)+"\n")
            index=index+1
            datalog.flush()
            led.value = not led.value
            print("write")
except OSError as e:  # Typically when the filesystem isn't writeable...
    delay = 1  # ...blink the LED every half second.
    if e.args[0] == 28:  # If the filesystem is full...
        delay = 0.25  # ...blink the LED faster!
    while True:
        led.value = not led.value
        time.sleep(delay)
