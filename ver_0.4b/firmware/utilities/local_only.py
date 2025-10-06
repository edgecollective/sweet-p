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

# mount the sd card and get the last line
try:
    sdcard = sdcardio.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")
    with open("/sd/log.txt", "r") as f:
        lines = f.readlines()
        last_line = lines[-1].strip().split(",")
    f.close()
except Exception as error:
    # handle the exception
    error_log = error_log+SDCARD_ERROR
    print("sd card error:", error)

print("last_line=",last_line)

if (len(last_line) < 2):
    # then populate sd card with fake data for next round
    sd_ts = "12/18/23 17, 0"
    try:
        with open("/sd/log.txt", "a") as f:
            #print("%d %0.1f %d\n" % (index,my_batt,my_depth))
            f.write(sd_ts+"\n")
            f.close()
    except Exception as error:
        # handle the exception
        error_log=error_log++SDCARD_ERROR
        print("sd card error", error)
        
    done_pin = digitalio.DigitalInOut(board.A3)
    done_pin.direction = digitalio.Direction.OUTPUT
    done_pin.value=True

else:
    last_date=last_line[0].strip()
    last_status=int(last_line[1].strip())

    # get the time from the GPS
            
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

    got_time = False

    while (got_time==False):
       
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
            if (int(gps.timestamp_utc.tm_year) == 0):
                print("waiting for full timestamp")
                continue
            
            
            sd_ts="{}/{}/{} {:02}:{:02}".format(
                    gps.timestamp_utc.tm_mon,  # Grab parts of the time from the
                    gps.timestamp_utc.tm_mday,  # struct_time object that holds
                    gps.timestamp_utc.tm_year,  # the fix time.  Note you might
                    gps.timestamp_utc.tm_hour,  # not get all data like year, day,
                    gps.timestamp_utc.tm_min,  # month!
                    #gps.timestamp_utc.tm_sec,
                )
            print("gps_time: ",sd_ts)
            
            hour = int(gps.timestamp_utc.tm_hour)
            nm_hour= hour-7;

            got_time = True
            
    # if here, we have the last date & status, and the time

    should_send = False
    send_result = 0

    # if we didn't send last time, then send

    if (last_status==0):
        should_send = True
        print("last send failed, so we should send this time!")
        
    else:

        #if(nm_hour == 5 or nm_hour == 1):          
        #write every hour; otherwise can put above condition on write
        print("last_date=",last_date)
        print("sd_ts=",sd_ts)
        
        if(last_date!=sd_ts):
            should_send = True
            print("new timestamp, so we should send this time!")
        else:
            print("same timestamp, shouldn't send")

    # send if we should
    
    if (should_send):

        print("SENDING")
        
        send_result = 1 # assume this for now; update from satellite code
        
        print("recording date & success")
        
        record = sd_ts + "," + str(send_result)+"\n"
        
        try:
            with open("/sd/log.txt", "a") as f:
                #print("%d %0.1f %d\n" % (index,my_batt,my_depth))
                f.write(record)
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

    
        
        
