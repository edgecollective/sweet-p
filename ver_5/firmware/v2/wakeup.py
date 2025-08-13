import time
import board
import adafruit_ds3231
import busio

# Initialize I2C using the same configuration as ds3231_simpletest.py
#i2c = board.I2C()  # uses board.SCL and board.SDA
i2c = busio.I2C(board.P0_11, board.P1_04)  # SCL, SDA
rtc = adafruit_ds3231.DS3231(i2c)

# Get current time
current_time = rtc.datetime
print("Current time:", current_time)

# Calculate alarm time (1 minutes from now)
alarm_minute = current_time.tm_min + 1
alarm_hour = current_time.tm_hour

# Handle minute overflow (if current minute + 2 >= 60)
if alarm_minute >= 60:
    alarm_minute -= 60
    alarm_hour += 1
    
    # Handle hour overflow (if hour + 1 >= 24)
    if alarm_hour >= 24:
        alarm_hour = 0

print(f"Setting alarm for {alarm_hour:02d}:{alarm_minute:02d}")

# Set alarm 1 to trigger at the calculated time
# DS3231 alarm expects (time, alarm_type) tuple
# alarm_type options: "once_per_second", "match_seconds", "match_minutes", "match_hours", "match_date", "match_day"
alarm_time = time.struct_time((
    current_time.tm_year,
    current_time.tm_mon, 
    current_time.tm_mday,
    alarm_hour,
    alarm_minute,
    0,  # seconds = 0
    current_time.tm_wday,
    current_time.tm_yday,
    current_time.tm_isdst
))

rtc.alarm1 = (alarm_time, "match_minutes")

# Configure alarm 1 to match on hours and minutes
# This sets the alarm to trigger when the RTC time matches the alarm time
rtc.alarm1_interrupt = True

# Enable alarm 1
rtc.alarm1_status = False  # Clear any existing alarm flag

print("Alarm set! SQW pin will go high when alarm triggers in 1 minute.")
print("Alarm time:", rtc.alarm1)
