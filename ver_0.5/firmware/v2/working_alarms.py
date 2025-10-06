import time
import board
import adafruit_ds3231
import busio

# Initialize I2C connection
i2c = busio.I2C(board.P0_11, board.P1_04)  # SCL, SDA
rtc = adafruit_ds3231.DS3231(i2c)

# Set the current time on the RTC (optional, if not already set)
# t = time.struct_time((2025, 8, 13, 18, 30, 0, 0, -1, -1)) # Year, Month, Day, Hour, Minute, Second, Weekday, Yearday, Is_DST
# rtc.datetime = t

# --- Setting Alarm 1 ---
# Set Alarm 1 to trigger at a specific time (e.g., 18:22:00 daily)
alarm1_time = time.struct_time((0, 0, 0, 18, 31, 0, 0, -1, -1)) # Year, Month, Day are ignored for daily alarms
rtc.alarm1 = (alarm1_time, "daily")

# Enable the interrupt pin for Alarm 1 (optional, if you want a physical interrupt)
rtc.alarm1_interrupt = True 

# --- Setting Alarm 2 ---
# Set Alarm 2 to trigger every minute at 0 seconds (e.g., 18:35:00, 18:36:00, etc.)
alarm2_time = time.struct_time((0, 0, 0, 0, 0, 0, 0, -1, -1)) # Only seconds are relevant for minutely alarms
rtc.alarm2 = (alarm2_time, "minutely")

# Enable the interrupt pin for Alarm 2 (optional)
rtc.alarm2_interrupt = True

print("Alarms set.")

# Main loop to check for alarms
while True:
    if rtc.alarm1_status:
        t = rtc.datetime
        print(f"Alarm 1 triggered at {t.tm_hour}:{t.tm_min:02}:{t.tm_sec:02}")
        t = rtc.datetime
        rtc.alarm1_status = False  # Reset the alarm status
    
    if rtc.alarm2_status:
        t = rtc.datetime
        print(f"Alarm 2 triggered at {t.tm_hour}:{t.tm_min:02}:{t.tm_sec:02}")
        rtc.alarm2_status = False  # Reset the alarm status
    
    time.sleep(1) # Check every second
