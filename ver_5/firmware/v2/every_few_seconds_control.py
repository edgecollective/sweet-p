import time
import board
import adafruit_ds3231
import busio
import digitalio

# Initialize I2C connection
i2c = busio.I2C(board.P0_11, board.P1_04)  # SCL, SDA
rtc = adafruit_ds3231.DS3231(i2c)

# the control pin
latch=digitalio.DigitalInOut(board.P0_09)
latch.direction=digitalio.Direction.OUTPUT
latch.value=False


# List of seconds within each minute when alarm1 should trigger
alarm_seconds = [20, 40]
current_alarm_index = 0

def find_closest_alarm_index(current_second):
    """Find the index of the closest alarm time in the list"""
    min_diff = float('inf')
    closest_index = 0
    
    for i, alarm_sec in enumerate(alarm_seconds):
        diff = abs(current_second - alarm_sec)
        if diff < min_diff:
            min_diff = diff
            closest_index = i
    
    return closest_index

def get_next_alarm_second():
    """Get the next alarm second in the sequence"""
    global current_alarm_index
    current_alarm_index = (current_alarm_index + 1) % len(alarm_seconds)
    return alarm_seconds[current_alarm_index]

def set_next_alarm():
    """Set alarm1 to trigger at the next second in the list"""
    next_second = get_next_alarm_second()
    
    # Set alarm to trigger at the next second in the current or next minute
    current_time = rtc.datetime
    
    # If the next alarm second has already passed this minute, set for next minute
    if next_second <= current_time.tm_sec:
        # We'll catch it next minute
        pass
    
    alarm1_time = time.struct_time((0, 0, 0, 0, 0, next_second, 0, -1, -1))
    rtc.alarm1 = (alarm1_time, "minutely")
    
    print(f"Next alarm set for {next_second} seconds")


# Set initial alarm to first item in the list
current_time = rtc.datetime
initial_second = alarm_seconds[current_alarm_index]

# If the first alarm time has already passed this minute, start with next one
if initial_second <= current_time.tm_sec:
    initial_second = get_next_alarm_second()

alarm1_time = time.struct_time((0, 0, 0, 0, 0, initial_second, 0, -1, -1))
rtc.alarm1 = (alarm1_time, "minutely")

# Enable the interrupt pin for Alarm 1
rtc.alarm1_interrupt = True 

print(f"Initial alarm set for {initial_second} seconds")
print(f"Alarm will trigger at seconds: {alarm_seconds}")

print("oscillator status:",rtc.disable_oscillator)

# Main loop to check for alarms
while True:
    try:
        # Only read time when needed to reduce I2C traffic
        if rtc.alarm1_status:
            t = rtc.datetime
            print(f"Alarm 1 triggered at {t.tm_hour}:{t.tm_min:02}:{t.tm_sec:02}")
            
            # Find which alarm was closest to trigger time
            closest_index = find_closest_alarm_index(t.tm_sec)
            current_alarm_index = closest_index
            
            print(f"Triggered at second {t.tm_sec}, closest to alarm second {alarm_seconds[closest_index]}")
            
            # Reset the alarm status
            rtc.alarm1_status = False
            
            # Set the next alarm
            set_next_alarm()
            
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
    
    time.sleep(1)  # Check every second
