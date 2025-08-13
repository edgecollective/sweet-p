import board
import busio
import time
import digitalio
import adafruit_ds3231

# Initialize I2C with your specific pins
i2c = busio.I2C(board.P0_11, board.P1_04)  # SCL, SDA

# Create the RTC instance
rtc = adafruit_ds3231.DS3231(i2c)

# Define the interrupt pin (change this to your actual interrupt pin)
# This is the pin that will go high when the alarm triggers
interrupt_pin = digitalio.DigitalInOut(board.P0_13)  # Change to your pin
interrupt_pin.direction = digitalio.Direction.OUTPUT
interrupt_pin.value = False  # Start with pin low

def set_rtc_time():
    """Set the current time on the DS3231"""
    # Set to current date/time
    # Format: (year, month, day, hour, minute, second, weekday, yearday, isdst)
    # weekday: 0=Monday through 6=Sunday
    # yearday: not used, set to -1
    # isdst: not used, set to -1
    
    # Example: Set to December 15, 2024, 14:30:00, Monday
    t = time.struct_time((2024, 12, 15, 14, 30, 0, 0, -1, -1))
    
    # Uncomment the line below to use the current system time instead
    # t = time.localtime()
    
    print(f"Setting RTC time to: {t}")
    rtc.datetime = t
    
    # Verify the time was set
    print(f"RTC time is now: {rtc.datetime}")

def set_alarm_minutes_from_now(minutes_from_now):
    """Set an alarm for X minutes from the current RTC time"""
    
    # Get current time from RTC
    current = rtc.datetime
    print(f"Current RTC time: {current}")
    
    # Calculate alarm time
    current_minutes = current.tm_min
    current_hours = current.tm_hour
    
    # Add the minutes
    alarm_minutes = current_minutes + minutes_from_now
    alarm_hours = current_hours
    
    # Handle minute overflow
    if alarm_minutes >= 60:
        alarm_hours += alarm_minutes // 60
        alarm_minutes = alarm_minutes % 60
    
    # Handle hour overflow (for simplicity, assumes alarm is within same day)
    if alarm_hours >= 24:
        alarm_hours = alarm_hours % 24
        print("Note: Alarm will be set for next day")
    
    # Clear any existing alarm flags
    rtc.alarm1_status = False
    rtc.alarm2_status = False
    
    # Set Alarm 1 (supports seconds precision)
    # alarm1 format: (seconds, minutes, hours, day/date)
    # Using None for day means "match any day"
    alarm_time = (0, alarm_minutes, alarm_hours, None)
    
    print(f"Setting alarm for: {alarm_hours:02d}:{alarm_minutes:02d}:00")
    rtc.alarm1 = alarm_time
    
    # Enable Alarm 1
    rtc.alarm1_interrupt = True
    
    return alarm_hours, alarm_minutes

def check_and_handle_alarm():
    """Check if alarm has triggered and handle it"""
    if rtc.alarm1_status:
        print("ALARM TRIGGERED!")
        
        # Pull the interrupt pin high
        interrupt_pin.value = True
        
        # Clear the alarm flag
        rtc.alarm1_status = False
        
        return True
    return False

def main():
    """Main program"""
    print("DS3231 RTC Alarm Setup")
    print("-" * 30)
    
    # Step 1: Set the RTC time
    set_rtc_time()
    print()
    
    # Step 2: Set an alarm for X minutes from now
    minutes_to_alarm = 2  # Change this to your desired minutes
    alarm_h, alarm_m = set_alarm_minutes_from_now(minutes_to_alarm)
    print(f"Alarm set for {minutes_to_alarm} minutes from now")
    print()
    
    # Step 3: Monitor for alarm
    print("Monitoring for alarm... (Press Ctrl+C to stop)")
    last_check = time.monotonic()
    
    try:
        while True:
            # Check alarm status
            if check_and_handle_alarm():
                print("Interrupt pin is now HIGH")
                
                # Keep pin high for 5 seconds then reset
                time.sleep(5)
                interrupt_pin.value = False
                print("Interrupt pin reset to LOW")
                
                # Optionally set a new alarm
                # set_alarm_minutes_from_now(minutes_to_alarm)
                
            # Display current time every 10 seconds
            if time.monotonic() - last_check >= 10:
                current = rtc.datetime
                print(f"Current time: {current.tm_hour:02d}:{current.tm_min:02d}:{current.tm_sec:02d}")
                print(f"Alarm status: {rtc.alarm1_status}")
                last_check = time.monotonic()
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nProgram stopped")
        # Clean up - disable alarms and reset pin
        rtc.alarm1_interrupt = False
        rtc.alarm2_interrupt = False
        interrupt_pin.value = False
        print("Alarms disabled and pin reset")

# Run the main program
if __name__ == "__main__":
    main()
