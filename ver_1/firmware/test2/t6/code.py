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

DEPTH_PIN = board.A0
depth_pin_adc = AnalogIn(DEPTH_PIN)

BATTERY_PIN = board.A1
battery_pin_adc = AnalogIn(BATTERY_PIN)
BATT_FACTOR=5.*1.15



sat_power_pin = digitalio.DigitalInOut(board.D9)
sat_power_pin.direction = digitalio.Direction.OUTPUT
sat_power_pin.value = False

# Compatibility with both CircuitPython 8.x.x and 9.x.x
try:
    from i2cdisplaybus import I2CDisplayBus
except ImportError:
    from displayio import I2CDisplay as I2CDisplayBus

# Configuration
WAKEUP_TIMES = [19,20,21]  # hours to wake up
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
        
        wakeup_area = label.Label(terminalio.FONT, text="", color=0xFFFF00, x=5, y=5)
        stats_area = label.Label(terminalio.FONT, text="", color=0xFFFF00, x=5, y=15)
        time_area = label.Label(terminalio.FONT, text="", color=0xFFFF00, x=5, y=25)
        status_area = label.Label(terminalio.FONT, text="", color=0xFFFF00, x=5, y=35)
        detail_area = label.Label(terminalio.FONT, text="", color=0xFFFF00, x=5, y=45)
        
        splash.append(wakeup_area)
        splash.append(stats_area)
        splash.append(time_area)
        splash.append(status_area)
        splash.append(detail_area)
        
        return wakeup_area, stats_area, time_area, status_area, detail_area
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

def update_display(wakeup_area, stats_area, time_area, status_area, detail_area, rtc, stats, status_msg="", detail_msg=""):
    """Update display with current information"""
    try:
        t = rtc.datetime
        wakeup_area.text = "wakeup: " + ' '.join(str(item) for item in WAKEUP_TIMES)
        stats_area.text = "stats: " + ' '.join(str(item) for item in stats)
        time_area.text = f"hr:{t.tm_hour:02} min:{t.tm_min:02} sec:{t.tm_sec:02}"
        status_area.text = status_msg
        detail_area.text = detail_msg
    except Exception as e:
        print(f"Display update failed: {e}")

def send_satellite_data(rb,data, display_areas=None):
    try:
        
    
        rb.data_out = data
        status=rb.satellite_transfer()

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

def main():
    """Main program logic"""
    # Initialize hardware (excluding RockBlock)
    i2c, display, eeprom, rtc = init_hardware()
    
    #clear_stats(eeprom)
    
    
    if not all([i2c, display, eeprom, rtc]):
        print("Critical hardware initialization failed!")
        return
    
    # Setup display
    wakeup_area, stats_area, time_area, status_area, detail_area = setup_display(display)
    if not all([wakeup_area, stats_area, time_area, status_area, detail_area]):
        print("Display setup failed!")
        return
    
    
                    
    # Get current time and stats
    try:
        t = rtc.datetime
        print(f"The date is {DAYS[int(t.tm_wday)]} {t.tm_mday}/{t.tm_mon}/{t.tm_year}")
        print(f"The time is {t.tm_hour}:{t.tm_min:02}:{t.tm_sec:02}")
        
        temp=rtc.temperature
        
        print("temperature=",temp)
        
        stats = read_from_eeprom(eeprom)
        update_display(wakeup_area, stats_area, time_area, status_area, detail_area, rtc, stats)
        
        
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
        
        # Send message if we've reached a send time
        if latest_send_time_index >= 0:
            # Initialize RockBlock only when we need to send
            update_display(wakeup_area, stats_area, time_area, status_area, detail_area, rtc, stats, "Initializing modem...", "")
            rb = init_rockblock()
            
            if rb is None:
                print("Failed to initialize RockBlock!")
                update_display(wakeup_area, stats_area, time_area, status_area, detail_area, rtc, stats, "Modem init failed", "Cannot send")
                return
            
            display_areas = (wakeup_area, stats_area, time_area, status_area, detail_area, rtc, stats)
            
            update_display(wakeup_area, stats_area, time_area, status_area, detail_area, rtc, stats, "Attempting to send...", "")
            
            #gather the data
            # fake for now
            batt_volts=7.
            #get battery level
            batt_volts=get_voltage(battery_pin_adc)*BATT_FACTOR
            batt_volts_str="{:.2f}".format(batt_volts)
            #text_area.text="Battery:\n"+batt_volts_str + " Volts"
            print("batt(V)="+batt_volts_str)
            
            
            depth_adc=depth_pin_adc.value
            print("depth_adc=",depth_adc)
            
            temperature=rtc.temperature
            
            
            attempt=1 # fake data
            error_log=1000 #fake data 
            
            data = struct.pack("f",batt_volts)
            data += struct.pack("i",depth_adc)
            data += struct.pack("i",attempt)
            data += struct.pack("f",temperature)
            data += struct.pack("i",error_log)
        
            #success = send_satellite_message(rb, "hello world", display_areas)
            success = send_satellite_data(rb, data, display_areas)
            
            if success:
                print("MESSAGE SENT")
                # Update stats for all send times up to and including current
                for i in range(latest_send_time_index + 1):
                    stats[i] = t.tm_mday
                write_to_eeprom(eeprom, stats)
                update_display(wakeup_area, stats_area, time_area, status_area, detail_area, rtc, stats, "Send successful", "Completed")
            else:
                print("MESSAGE FAILED TO SEND")
                update_display(wakeup_area, stats_area, time_area, status_area, detail_area, rtc, stats, "Send failed", "Max retries reached")
            
            # Power down RockBlock after use
            sat_power_pin.value = False
        else:
            update_display(wakeup_area, stats_area, time_area, status_area, detail_area, rtc, stats, "Not time to send", "")
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
   
    main()
    # Sleeping
    #done_pin = digitalio.DigitalInOut(board.D7)
        #done_pin.direction = digitalio.Direction.OUTPUT
    #done_pin.value = True
