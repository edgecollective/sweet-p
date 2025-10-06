import time
import board
import adafruit_ds3231
import busio

# Initialize I2C connection
i2c = busio.I2C(board.P0_11, board.P1_04)  # SCL, SDA
rtc = adafruit_ds3231.DS3231(i2c)

# List of minutes within each hour when alarm1 should trigger
alarm_minutes = [54, 56,58]
current_alarm_index = 0

def find_closest_alarm_index(current_minute):
    """Find the index of the closest alarm time in the list"""
    min_diff = float('inf')
    closest_index = 0
    
    for i, alarm_min in enumerate(alarm_minutes):
        diff = abs(current_minute - alarm_min)
        if diff < min_diff:
            min_diff = diff
            closest_index = i
    
    return closest_index

def get_next_alarm_minute():
    """Get the next alarm minute in the sequence"""
    global current_alarm_index
    current_alarm_index = (current_alarm_index + 1) % len(alarm_minutes)
    return alarm_minutes[current_alarm_index]

def set_next_alarm():
    """Set alarm1 to trigger at the next minute in the list"""
    next_minute = get_next_alarm_minute()
    
    # Set alarm to trigger at the next minute in the current or next hour
    current_time = rtc.datetime
    
    # If the next alarm minute has already passed this hour, set for next hour
    if next_minute <= current_time.tm_min:
        # We'll catch it next hour
        pass
    
    alarm1_time = time.struct_time((0, 0, 0, 0, next_minute, 0, 0, -1, -1))
    rtc.alarm1 = (alarm1_time, "hourly")
    
    print(f"Next alarm set for minute {next_minute}")

# Set initial alarm to first item in the list
current_time = rtc.datetime
initial_minute = alarm_minutes[current_alarm_index]

# If the first alarm time has already passed this hour, start with next one
if initial_minute <= current_time.tm_min:
    initial_minute = get_next_alarm_minute()

alarm1_time = time.struct_time((0, 0, 0, 0, initial_minute, 0, 0, -1, -1))
rtc.alarm1 = (alarm1_time, "hourly")

# Enable the interrupt pin for Alarm 1
rtc.alarm1_interrupt = True 

print(f"Initial alarm set for minute {initial_minute}")
print(f"Alarm will trigger at minutes: {alarm_minutes}")

# Main loop to check for alarms
while True:
    if rtc.alarm1_status:
        t = rtc.datetime
        print(f"Alarm 1 triggered at {t.tm_hour}:{t.tm_min:02}:{t.tm_sec:02}")
        
        # Find which alarm was closest to trigger time
        closest_index = find_closest_alarm_index(t.tm_min)
        current_alarm_index = closest_index
        
        print(f"Triggered at minute {t.tm_min}, closest to alarm minute {alarm_minutes[closest_index]}")
        
        # Reset the alarm status
        rtc.alarm1_status = False
        
        # Set the next alarm
        set_next_alarm()
    
    time.sleep(1)  # Check every second
