import board
import struct
import adafruit_24lc32
import adafruit_ds3231
import time

# Initialize I2C and EEPROM
i2c = board.I2C()
eeprom = adafruit_24lc32.EEPROM_I2C(i2c, address=0x57)

rtc = adafruit_ds3231.DS3231(i2c)

# 4 integers to write to EEPROM
#wakeup_stats = [5, 13, 18, 25]  #hour1, hour2, hour3, day of month

days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

wakeup_times = [15, 30, 45]  #these are the seconds to wake up

wakeup_stats = [0, 0, 0] #these record the last minute that each item was sent

def write_to_eeprom(integers_to_write):
    # Convert integers to bytes and write to EEPROM
    # Each integer takes 4 bytes, so we'll use addresses 0, 4, 8, 12
    print("Writing integers to EEPROM...")
    print(f"Original integers: {integers_to_write}")
    
    for i, value in enumerate(integers_to_write):
        # Pack integer as 4-byte signed integer (little-endian)
        byte_data = struct.pack('<i', value)
        start_addr = i * 4
        
        # Write the 4 bytes to EEPROM
        for j, byte in enumerate(byte_data):
            eeprom[start_addr + j] = byte
        
        print(f"Wrote integer {value} to EEPROM at address {start_addr}")
    
def read_from_eeprom():
    print("\nReading integers from EEPROM...")

    # Read back the integers
    retrieved_integers = []
    for i in range(3):
        start_addr = i * 4
        
        # Read 4 bytes from EEPROM as a slice (returns bytearray)
        byte_data = eeprom[start_addr:start_addr + 4]
        
        # Unpack bytes back to integer
        retrieved_value = struct.unpack('<i', byte_data)[0]
        retrieved_integers.append(retrieved_value)
        
        print(f"Read integer {retrieved_value} from EEPROM at address {start_addr}")
    
    return(retrieved_integers)

# wakup and check the time

t = rtc.datetime

print(
        "The date is {} {}/{}/{}".format(
            days[int(t.tm_wday)], t.tm_mday, t.tm_mon, t.tm_year
        )
    )
print("The time is {}:{:02}:{:02}".format(t.tm_hour, t.tm_min, t.tm_sec))

print("the minute is {:02}".format(t.tm_min))

print("the hour is {:02}".format(t.tm_hour))

#write_to_eeprom([0,0,0])

stats = read_from_eeprom()

while True:

    t = rtc.datetime
    
    print("---------------------------------")
    print("wakeup_times=",wakeup_times)
    
    print("the minute is {:02}".format(t.tm_min))
    
    print("the second is {:02}".format(t.tm_sec))
    

    try:
        index=wakeup_times.index(t.tm_sec)
        print("item #",index)
        # if we got here, then the item is in the list
        if(stats[index]!=t.tm_min): # then we didn't broadcast for this second of the minute
            print("should broadcast!")
            stats[index]=t.tm_min
        
    except:
        print("not in list")
        
    
    print("stats:",stats)

    time.sleep(.7)
        



    


