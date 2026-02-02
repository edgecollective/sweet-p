import board
import struct
import time
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_24lc32
import adafruit_ds3231
import adafruit_displayio_ssd1306
from adafruit_rockblock import RockBlock
import digitalio
import sys
from analogio import AnalogIn
import supervisor

TIMEZONE_OFFSET_HOURS = -5  # EST offset from UTC (change to -4 for EDT)

supervisor.runtime.autoreload = False

button_A_pin = digitalio.DigitalInOut(board.A5)
button_A_pin.direction = digitalio.Direction.INPUT
button_pressed=False

if(button_A_pin.value): #i.e. if button is pressed in our circuit, the value will be 'False'
    button_pressed=False
    print("button not pressed")
else:
    button_pressed=True
    print("button pressed!")
    #led.value=True

BATTERY_PIN = board.A3
battery_pin_adc = AnalogIn(BATTERY_PIN)
BATT_FACTOR=2.*1.91

probe_power_pin = digitalio.DigitalInOut(board.D10)
probe_power_pin.direction = digitalio.Direction.OUTPUT
probe_power_pin.value = False

probe_adc = AnalogIn(board.A2)
NUM_AVE = 10
TIME_SPACING = 1

PROBE_WAKEUP_TIME = 5 #seconds required for probe to warm up to make measurement


sat_power_pin = digitalio.DigitalInOut(board.D9)
sat_power_pin.direction = digitalio.Direction.OUTPUT
sat_power_pin.value = False

# Compatibility with both CircuitPython 8.x.x and 9.x.x
try:
    from i2cdisplaybus import I2CDisplayBus
except ImportError:
    from displayio import I2CDisplay as I2CDisplayBus

# Configuration
#WAKEUP_TIMES = [5,13,18]  # hours to wake up
WAKEUP_TIMES = [9,10,11]  # hours to wake up
MAX_RETRY = 4
SLEEP_BETWEEN = 5
DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")



def get_voltage(pin):
    return (pin.value * 3.3) / 65536


def init_hardware():
    """Initialize hardware components (without RockBlock modem)"""
    #try:
    # Initialize I2C
    i2c = board.I2C()

    # Initialize display
    displayio.release_displays()
    display_bus = I2CDisplayBus(i2c, device_address=0x3C)
    display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

    # Initialize EEPROM and RTC
    eeprom = adafruit_24lc32.EEPROM_I2C(i2c, address=0x57)
    rtc = adafruit_ds3231.DS3231(i2c)

    return i2c, display, eeprom, rtc
    #except Exception as e:
    #    print(f"Hardware initialization failed: {e}")
    #    return None, None, None, None

def init_rockblock():
    """Initialize RockBlock modem only when needed"""
    try:
        sat_power_pin.value = True
        time.sleep(3)
        uart = board.UART()
        uart.baudrate = 19200
        rb = RockBlock(uart)
        return rb
    except Exception as e:
        print(f"RockBlock initialization failed: {e}")
        return None

def setup_display(display):
    """Setup display with labels"""
    try:
        splash = displayio.Group()
        display.root_group = splash

        stats_area = label.Label(terminalio.FONT, text="", color=0xFFFF00, x=5, y=5)
        time_area = label.Label(terminalio.FONT, text="", color=0xFFFF00, x=5, y=15)
        temp_batt_area = label.Label(terminalio.FONT, text="", color=0xFFFF00, x=5, y=25)
        probe_area = label.Label(terminalio.FONT, text="", color=0xFFFF00, x=5, y=35)
        satellite_area = label.Label(terminalio.FONT, text="", color=0xFFFF00, x=5, y=45)

        splash.append(stats_area)
        splash.append(time_area)
        splash.append(temp_batt_area)
        splash.append(probe_area)
        splash.append(satellite_area)

        return stats_area, time_area, temp_batt_area, probe_area, satellite_area
    except Exception as e:
        print(f"Display setup failed: {e}")
        return None, None, None, None, None

def clear_stats(eeprom):
    stats=[0,0,0]
    write_to_eeprom(eeprom,stats)

def write_to_eeprom(eeprom, integers_to_write):
    """Write integers to EEPROM with error handling"""
    try:
        print(f"Writing to EEPROM: {integers_to_write}")
        for i, value in enumerate(integers_to_write):
            byte_data = struct.pack('<i', value)
            start_addr = i * 4
            for j, byte in enumerate(byte_data):
                eeprom[start_addr + j] = byte
        return True
    except Exception as e:
        print(f"EEPROM write failed: {e}")
        return False

def read_from_eeprom(eeprom):
    """Read integers from EEPROM with error handling"""
    try:
        print("Reading from EEPROM...")
        retrieved_integers = []
        for i in range(3):
            start_addr = i * 4
            byte_data = eeprom[start_addr:start_addr + 4]
            retrieved_value = struct.unpack('<i', byte_data)[0]
            retrieved_integers.append(retrieved_value)
        return retrieved_integers
    except Exception as e:
        print(f"EEPROM read failed: {e}")
        return [0, 0, 0]  # Return default values

def update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp=None, batt_volts=None, probe_msg="", satellite_msg=""):
    """Update display with current information"""
    try:
        t = rtc.datetime
        stats_area.text = "s: "+str(WAKEUP_TIMES[0])+":"+str(stats[0])+" "+ str(WAKEUP_TIMES[1])+":"+str(stats[1])+" "+ str(WAKEUP_TIMES[2])+":"+str(stats[2])
        time_area.text = f"{t.tm_mon:02}/{t.tm_mday:02}/{t.tm_year%100:02} {t.tm_hour:02}:{t.tm_min:02}:{t.tm_sec:02} {TIMEZONE_OFFSET_HOURS:+d}"

        # Temperature and battery line
        temp_batt_text = ""
        if temp is not None:
            # Convert Celsius to Fahrenheit for display
            temp_f = (temp * 9/5) + 32
            temp_batt_text += f"T:{temp_f:.1f}F "
        if batt_volts is not None:
            temp_batt_text += f"B:{batt_volts:.2f}V"
        temp_batt_area.text = temp_batt_text

        probe_area.text = probe_msg
        satellite_area.text = satellite_msg
    except Exception as e:
        print(f"Display update failed: {e}")

def send_satellite_data(rb,data, display_areas=None):
    try:


        rb.data_out = data
        status=rb.satellite_transfer()

        if display_areas:
            stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts = display_areas
            # Preserve existing probe_area text and show satellite status in satellite_area
            preserved_probe = probe_area.text
            update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats,
                          temp, batt_volts, preserved_probe, f"Initial Status: {status[0]}")

        retry = 0
        while status[0] > 8 and retry < MAX_RETRY:
            status = rb.satellite_transfer()
            print(f"Retry {retry}, status: {status}")

            if display_areas:
                update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats,
                              temp, batt_volts, preserved_probe, f"Retry {retry+1}/{MAX_RETRY} Status: {status[0]}")

            retry += 1
            time.sleep(SLEEP_BETWEEN)

        return status[0] <= 8

    except Exception as e:
        print(f"Satellite communication failed: {e}")
        return False

def get_ave_probe_adc(display_areas=None):
    if display_areas:
        stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts = display_areas
        update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts, "Measuring depth...", "Warming up...")

    print("turning on probe...")
    probe_power_pin.value = True
    print("waiting for probe to warm up...")
    time.sleep(PROBE_WAKEUP_TIME)

    if display_areas:
        update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts, "Measuring depth...", "Getting average...")

    print("getting average adc value for probe...")

    ave_probe_adc=0.

    for i in range(0,NUM_AVE):

        #probe_power_pin.value = False
        #print("D10 off")
        ave_probe_adc = ave_probe_adc + probe_adc.value

        time.sleep(TIME_SPACING)

    ave_probe_adc=int(ave_probe_adc/float(NUM_AVE))

    print("ave_probe_adc=",ave_probe_adc)

    if display_areas:
        update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts, f"Ave probe ADC: {ave_probe_adc}", "Attempting to send...")

        # Countdown display
        for countdown in range(8, 0, -1):
            update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts, f"Ave probe ADC: {ave_probe_adc}", f"Sending in {countdown} sec")
            time.sleep(1)
    else:
        time.sleep(8)

    print("turning off probe")
    probe_power_pin.value = False
    return(ave_probe_adc)

def sync_time_from_satellite(rb, rtc, display_areas=None):
    """Sync RTC time from satellite network with timezone offset - DEBUG VERSION"""
    try:
        if display_areas:
            stats_area, time_area, temp_batt_area, probe_area, satellite_area, _, stats, temp, batt_volts = display_areas
            update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts, "Time sync", "Connecting to network...")

        print("=" * 50)
        print("DEBUG: Starting time sync from satellite")
        print("=" * 50)

        # First, show what the RTC currently has
        current_rtc = rtc.datetime
        print(f"DEBUG: RTC BEFORE sync: {current_rtc.tm_year}-{current_rtc.tm_mon:02}-{current_rtc.tm_mday:02} {current_rtc.tm_hour:02}:{current_rtc.tm_min:02}:{current_rtc.tm_sec:02}")

        print("Attempting to get time from satellite network...")

        # Get system time from satellite network (UTC)
        sat_time_utc = rb.system_time

        if sat_time_utc:
            # DEBUG: Print raw satellite time
            print(f"DEBUG: Raw satellite struct_time: {sat_time_utc}")
            print(f"DEBUG: Satellite date: {sat_time_utc.tm_year}-{sat_time_utc.tm_mon:02}-{sat_time_utc.tm_mday:02}")
            print(f"DEBUG: Satellite time (should be UTC): {sat_time_utc.tm_hour:02}:{sat_time_utc.tm_min:02}:{sat_time_utc.tm_sec:02}")
            print(f"DEBUG: TIMEZONE_OFFSET_HOURS = {TIMEZONE_OFFSET_HOURS}")

            if display_areas:
                update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts, "Time sync", "Converting to local...")

            # Convert UTC to local time by applying timezone offset
            import time as time_module

            # Convert struct_time to timestamp, apply offset, convert back
            utc_timestamp = time_module.mktime(sat_time_utc)
            print(f"DEBUG: UTC timestamp from mktime(): {utc_timestamp}")

            local_timestamp = utc_timestamp + (TIMEZONE_OFFSET_HOURS * 3600)  # 3600 seconds = 1 hour
            print(f"DEBUG: Local timestamp (after adding {TIMEZONE_OFFSET_HOURS} hours): {local_timestamp}")
            print(f"DEBUG: Offset applied: {TIMEZONE_OFFSET_HOURS * 3600} seconds")

            local_time = time_module.localtime(local_timestamp)
            print(f"DEBUG: Calculated local struct_time: {local_time}")
            print(f"DEBUG: Calculated local time: {local_time.tm_hour:02}:{local_time.tm_min:02}:{local_time.tm_sec:02}")

            if display_areas:
                update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts, "Time sync", "Setting RTC...")

            # Set the RTC with the local time
            rtc.datetime = local_time

            # DEBUG: Verify what was actually stored
            time_module.sleep(0.5)  # Small delay to ensure RTC is updated
            verify_time = rtc.datetime
            print(f"DEBUG: RTC AFTER sync: {verify_time.tm_year}-{verify_time.tm_mon:02}-{verify_time.tm_mday:02} {verify_time.tm_hour:02}:{verify_time.tm_min:02}:{verify_time.tm_sec:02}")
            print("=" * 50)
            print("DEBUG: COMPARE THE ABOVE TO YOUR ACTUAL EST TIME!")
            print("DEBUG: If RTC shows 4 hours behind, the satellite time")
            print("DEBUG: is likely already offset (not pure UTC).")
            print("=" * 50)

            if display_areas:
                update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts, "Time sync", "Local time set!")

            print(f"RTC time successfully updated to local time (UTC{TIMEZONE_OFFSET_HOURS:+d})")
            return True
        else:
            print("Failed to get time from satellite network")
            print("DEBUG: rb.system_time returned None")

            if display_areas:
                update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts, "Time sync", "Sync failed")

            return False

    except Exception as e:
        print(f"Time sync failed: {e}")
        import sys
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if exc_traceback:
            print(f"DEBUG: Exception at line {exc_traceback.tb_lineno}")

        if display_areas:
            stats_area, time_area, temp_batt_area, probe_area, satellite_area, _, stats, temp, batt_volts = display_areas
            update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts, "Time sync", f"Error: {e}")

        return False

def send_satellite_message(rb, message, display_areas=None):
    """Send message via satellite with retry logic"""
    try:
        rb.text_out = message
        print("Talking to satellite...")
        status = rb.satellite_transfer()

        if display_areas:
            wakeup_area, stats_area, time_area, status_area, detail_area, rtc, stats = display_areas
            update_display(wakeup_area, stats_area, time_area, status_area, detail_area, rtc, stats,
                          "Attempting send...", f"Initial Status: {status[0]}")

        retry = 0
        while status[0] > 8 and retry < MAX_RETRY:
            status = rb.satellite_transfer()
            print(f"Retry {retry}, status: {status}")

            if display_areas:
                update_display(wakeup_area, stats_area, time_area, status_area, detail_area, rtc, stats,
                              "Attempting send...", f"Retry {retry+1}/{MAX_RETRY} Status: {status[0]}")

            retry += 1
            time.sleep(SLEEP_BETWEEN)

        return status[0] <= 8
    except Exception as e:
        print(f"Satellite communication failed: {e}")
        return False

def probe_test():

    FORCE_SEND=False
    # Initialize hardware (excluding RockBlock)
    i2c, display, eeprom, rtc = init_hardware()

    #clear_stats(eeprom)


    if not all([i2c, display, eeprom, rtc]):
        print("Critical hardware initialization failed!")
        return

    # Setup display
    stats_area, time_area, temp_batt_area, probe_area, satellite_area = setup_display(display)
    if not all([stats_area, time_area, temp_batt_area, probe_area, satellite_area]):
        print("Display setup failed!")
        return

    # Get temperature and battery voltage early for display
    temp = rtc.temperature
    print("temperature=", temp)

    batt_volts = get_voltage(battery_pin_adc) * BATT_FACTOR
    batt_volts_str = "{:.2f}".format(batt_volts)
    print("batt(V)=" + batt_volts_str)

    if(button_pressed):
        print("force send!")
        FORCE_SEND=True
        #update_display(wakeup_area, stats_area, time_area, status_area, detail_area, rtc, stats, "Force send!", "")

        time.sleep(2)


    # Get current time and stats
    try:
        t = rtc.datetime
        print(f"The date is {DAYS[int(t.tm_wday)]} {t.tm_mday}/{t.tm_mon}/{t.tm_year}")
        print(f"The time is {t.tm_hour}:{t.tm_min:02}:{t.tm_sec:02}")

        stats = read_from_eeprom(eeprom)

        if(FORCE_SEND):
            update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts, "Force send!", "")
        else:
            update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts)
        time.sleep(2)


        # Find the latest send time we've passed
        latest_send_time_index = -1
        for i in range(len(WAKEUP_TIMES)):
            this_hour=WAKEUP_TIMES[i]

            print("this_hour=",this_hour)
            print("t.tm_hour=",t.tm_hour)
            print("t.tm_mday=",t.tm_mday)
            print("stats[i]=",stats[i])

            if (int(this_hour)<=int(t.tm_hour)) and (stats[i]!=t.tm_mday):
                latest_send_time_index=i
                print("set latest_send_time_index to:",latest_send_time_index)



        #for i, wake_minute in enumerate(WAKEUP_TIMES):
        #    if wake_minute <= t.tm_min:
        #        latest_send_time_index = i

        print(f"Latest send time index: {latest_send_time_index}")

        # Send message if we've reached a send time or if FORCE_SEND==True

        #if latest_send_time_index >= 0 or FORCE_SEND==True:
            # Initialize RockBlock only when we need to send

        display_areas = (stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts)
        
        while True:

            depth_adc=get_ave_probe_adc(display_areas)
            print(depth_adc)

    except Exception as e:
        print(f"Probe test error: {e}")

def main():
    """Main program logic"""

    FORCE_SEND=False
    # Initialize hardware (excluding RockBlock)
    i2c, display, eeprom, rtc = init_hardware()

    #clear_stats(eeprom)


    if not all([i2c, display, eeprom, rtc]):
        print("Critical hardware initialization failed!")
        return

    # Setup display
    stats_area, time_area, temp_batt_area, probe_area, satellite_area = setup_display(display)
    if not all([stats_area, time_area, temp_batt_area, probe_area, satellite_area]):
        print("Display setup failed!")
        return

    # Get temperature and battery voltage early for display
    temp = rtc.temperature
    print("temperature=", temp)

    batt_volts = get_voltage(battery_pin_adc) * BATT_FACTOR
    batt_volts_str = "{:.2f}".format(batt_volts)
    print("batt(V)=" + batt_volts_str)

    if(button_pressed):
        print("force send!")
        FORCE_SEND=True
        #update_display(wakeup_area, stats_area, time_area, status_area, detail_area, rtc, stats, "Force send!", "")

        time.sleep(2)


    # Get current time and stats
    try:
        t = rtc.datetime
        print(f"The date is {DAYS[int(t.tm_wday)]} {t.tm_mday}/{t.tm_mon}/{t.tm_year}")
        print(f"The time is {t.tm_hour}:{t.tm_min:02}:{t.tm_sec:02}")

        stats = read_from_eeprom(eeprom)

        if(FORCE_SEND):
            update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts, "Force send!", "")
        else:
            update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts)
        time.sleep(2)


        # Find the latest send time we've passed
        latest_send_time_index = -1
        for i in range(len(WAKEUP_TIMES)):
            this_hour=WAKEUP_TIMES[i]

            print("this_hour=",this_hour)
            print("t.tm_hour=",t.tm_hour)
            print("t.tm_mday=",t.tm_mday)
            print("stats[i]=",stats[i])

            if (int(this_hour)<=int(t.tm_hour)) and (stats[i]!=t.tm_mday):
                latest_send_time_index=i
                print("set latest_send_time_index to:",latest_send_time_index)



        #for i, wake_minute in enumerate(WAKEUP_TIMES):
        #    if wake_minute <= t.tm_min:
        #        latest_send_time_index = i

        print(f"Latest send time index: {latest_send_time_index}")

        # Send message if we've reached a send time or if FORCE_SEND==True

        if latest_send_time_index >= 0 or FORCE_SEND==True:
            # Initialize RockBlock only when we need to send

            display_areas = (stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts)

            update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts, "Measuring depth...", "")


            print("getting average probe depth...")

            depth_adc=get_ave_probe_adc(display_areas)

            print("depth_adc=",depth_adc)

            # now send via modem

            update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts, f"Ave probe ADC: {depth_adc}", "Initializing modem...")
            rb = init_rockblock()

            if rb is None:
                print("Failed to initialize RockBlock!")
                update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts, f"Ave probe ADC: {depth_adc}", "Modem init failed")
                return



            update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts, f"Ave probe ADC: {depth_adc}", "Attempting to send...")

            #gather the data
            # fake for now
            #batt_volts=7.
            #get battery level



            attempt=1 # fake data
            error_log=1000 #fake data

            data = struct.pack("f",batt_volts)
            data += struct.pack("i",depth_adc)
            data += struct.pack("i",attempt)
            data += struct.pack("f",temp)
            data += struct.pack("i",error_log)

            #success = send_satellite_message(rb, "hello world", display_areas)
            success = send_satellite_data(rb, data, display_areas)

            if success:
                print("MESSAGE SENT")

                # Sync RTC time from satellite network after successful send
                print("Syncing time from satellite network...")
                update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts, f"Ave probe ADC: {depth_adc}", "Syncing time...")
                time_sync_success = sync_time_from_satellite(rb, rtc, display_areas)

                if time_sync_success:
                    print("Time sync successful")
                    update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts, f"Ave probe ADC: {depth_adc}", "Send & sync successful")
                else:
                    print("Time sync failed")
                    update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts, f"Ave probe ADC: {depth_adc}", "Send ok, sync failed")

                # Update stats for all send times up to and including current
                if not FORCE_SEND:  # Only update stats for scheduled sends, not force sends
                    for i in range(latest_send_time_index + 1):
                        stats[i] = t.tm_mday
                    write_to_eeprom(eeprom, stats)
            else:
                print("MESSAGE FAILED TO SEND")
                update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts, f"Ave probe ADC: {depth_adc}", "Send failed")

            # Power down RockBlock after use
            sat_power_pin.value = False
        else:
            update_display(stats_area, time_area, temp_batt_area, probe_area, satellite_area, rtc, stats, temp, batt_volts, "", "Not time to send")
            time.sleep(5)

    except Exception as e:
        print(f"Main execution error: {e}")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = exc_traceback.tb_lineno
        print(f"An exception occurred at line: {line_number}")
        print(f"Exception details: {e}")

    time.sleep(5) # to allow for us to see the display

    done_pin = digitalio.DigitalInOut(board.D7)
    done_pin.direction = digitalio.Direction.OUTPUT
    done_pin.value = True

if __name__ == "__main__":

    #main()
    probe_test()
    # Sleeping
    #done_pin = digitalio.DigitalInOut(board.D7)
        #done_pin.direction = digitalio.Direction.OUTPUT
    #done_pin.value = True
