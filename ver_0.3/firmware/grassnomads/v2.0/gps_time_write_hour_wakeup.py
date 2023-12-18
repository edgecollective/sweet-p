# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# Simple GPS module demonstration.
# Will wait for a fix and print a message every second with the current location
# and other details.
import time
import board
import busio
import sdcardio
import storage
import adafruit_gps
import digitalio

spi = board.SPI()
cs = board.D10

try:
    sdcard = sdcardio.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")
except Exception as error:
    # handle the exception
    error_log = error_log+SDCARD_ERROR
    print("sd card error:", error)

# If using I2C, we'll create an I2C interface to talk to using default pins
i2c = board.I2C()  # uses board.SCL and board.SDA

# Create a GPS module instance.
gps = adafruit_gps.GPS_GtopI2C(i2c, debug=False)  # Use I2C interface

# Turn on the basic GGA and RMC info (what you typically want)
gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")

# Set update rate to once a second (1hz) which is what you typically want.
gps.send_command(b"PMTK220,1000")

# Main loop runs forever printing the location, etc. every second.
last_print = time.monotonic()
while True:
   
    gps.update()
    # Every second print out current location details if there's a fix.
    current = time.monotonic()
    if current - last_print >= 1.0:
        last_print = current
        if not gps.has_fix:
            # Try again if we don't have a fix yet.
            print("Waiting for fix...")
            continue
        # We have a fix! (gps.has_fix is true)
        # Print out details about the fix like location, date, etc.
        print("=" * 40)  # Print a separator line.
        print(
            "Fix timestamp: {}/{}/{} {:02}:{:02}:{:02}".format(
                gps.timestamp_utc.tm_mon,  # Grab parts of the time from the
                gps.timestamp_utc.tm_mday,  # struct_time object that holds
                gps.timestamp_utc.tm_year,  # the fix time.  Note you might
                gps.timestamp_utc.tm_hour,  # not get all data like year, day,
                gps.timestamp_utc.tm_min,  # month!
                gps.timestamp_utc.tm_sec,
            )
        )
        if (int(gps.timestamp_utc.tm_year) == 0):
            print("waiting for full timestamp")
            continue
            
        sd_ts="{}/{}/{} {:02}".format(
                gps.timestamp_utc.tm_mon,  # Grab parts of the time from the
                gps.timestamp_utc.tm_mday,  # struct_time object that holds
                gps.timestamp_utc.tm_year,  # the fix time.  Note you might
                gps.timestamp_utc.tm_hour,  # not get all data like year, day,
                #gps.timestamp_utc.tm_min,  # month!
                #gps.timestamp_utc.tm_sec,
            )
            
        hour = int(gps.timestamp_utc.tm_hour)
        nm_hour= hour-7;
        print("hour = ",hour)
        print("nm_hour=",nm_hour)
        
        print("sd_ts=",sd_ts)
        
        #if(nm_hour == 5 or nm_hour == 1):          
        # write every hour; otherwise can put above condition on write
        
        try:
            with open("/sd/log.txt", "r") as f:
                lines = f.readlines()
                last_line = lines[-1]
                
                print("last_line=",last_line)
                f.close()
                
        except Exception as error:
            # handle the exception
            error_log = error_log++SDCARD_ERROR
            print("sd card error", error)
    
        if(last_line.strip()==sd_ts.strip()):
            print("same hour; skipping")
            
        else:
            print("writing new hour")
            try:
                with open("/sd/log.txt", "a") as f:
                    #print("%d %0.1f %d\n" % (index,my_batt,my_depth))
                    f.write(sd_ts+"\n")
                    f.close()
            except Exception as error:
                # handle the exception
                error_log=error_log++SDCARD_ERROR
                print("sd card error", error)
        
        print("sleeping ...")
        time.sleep(2)   
        done_pin = digitalio.DigitalInOut(board.A3)
        done_pin.direction = digitalio.Direction.OUTPUT
        done_pin.value=True
        
    
        
        
