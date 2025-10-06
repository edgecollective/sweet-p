import time
import board
import adafruit_ds3231
import busio
import digitalio

# Initialize I2C connection
i2c = busio.I2C(board.SCL, board.SDA)  # SCL, SDA
rtc = adafruit_ds3231.DS3231(i2c)


led=digitalio.DigitalInOut(board.LED)
led.direction=digitalio.Direction.OUTPUT
led.value=False

# List of seconds within each minute when alarm1 should trigger
alarm_seconds = 20


def set_next_alarm(next_second):
    """Set alarm1 to trigger at the next second in the list"""
    
    alarm1_time = time.struct_time((0, 0, 0, 0, 0, next_second, 0, -1, -1))
    rtc.alarm1 = (alarm1_time, "minutely")
    
    print(f"Next alarm set for {next_second} seconds")

set_next_alarm(alarm_seconds)


print(f"Initial alarm set for {alarm_seconds} seconds")
print(f"Alarm will trigger at seconds: {alarm_seconds}")

rtc.alarm1_interrupt = True 

print("enabled alarm interrupt")

print("oscillator status:",rtc.disable_oscillator)



