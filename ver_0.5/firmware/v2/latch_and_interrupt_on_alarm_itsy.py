import time
import board
import adafruit_ds3231
import busio
import digitalio

# Initialize I2C connection
i2c = busio.I2C(board.SCL, board.SDA)  # SCL, SDA
rtc = adafruit_ds3231.DS3231(i2c)

# the control pin
latch=digitalio.DigitalInOut(board.D9)
latch.direction=digitalio.Direction.OUTPUT
latch.value=False

led=digitalio.DigitalInOut(board.LED)
led.direction=digitalio.Direction.OUTPUT
led.value=False

# Main loop to check for alarms
print("oscillator status:",rtc.disable_oscillator)


while True:
    try:
        # Only read time when needed to reduce I2C traffic
        if rtc.alarm1_status:
            t = rtc.datetime
            print(f"Alarm 1 triggered at {t.tm_hour}:{t.tm_min:02}:{t.tm_sec:02}")
            
            rtc.alarm1_status = False
            print("reset alarm.")
            
            print("waiting 3 seconds ...")
            time.sleep(3)
            print("Turning off the light")
            latch.value=True
            time.sleep(0.1)
            latch.value=False
        
    except OSError as e:
        print(f"I2C error: {e}")
        time.sleep(2)  # Wait longer on I2C errors
        continue
    
    led.value=True
    time.sleep(.1)
    led.value=False
    time.sleep(1)  # Check every second
