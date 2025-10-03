import board
import struct
import adafruit_24lc32

# Initialize I2C and EEPROM
i2c = board.I2C()
eeprom = adafruit_24lc32.EEPROM_I2C(i2c, address=0x57)

# 4 integers to write to EEPROM
integers_to_write = [1234, -5678, 42, 999999]

print("Writing integers to EEPROM...")
print(f"Original integers: {integers_to_write}")

# Convert integers to bytes and write to EEPROM
# Each integer takes 4 bytes, so we'll use addresses 0, 4, 8, 12
for i, value in enumerate(integers_to_write):
    # Pack integer as 4-byte signed integer (little-endian)
    byte_data = struct.pack('<i', value)
    start_addr = i * 4
    
    # Write the 4 bytes to EEPROM
    for j, byte in enumerate(byte_data):
        eeprom[start_addr + j] = byte
    
    print(f"Wrote integer {value} to EEPROM at address {start_addr}")

print("\nReading integers from EEPROM...")

# Read back the integers
retrieved_integers = []
for i in range(4):
    start_addr = i * 4
    
    # Read 4 bytes from EEPROM as a slice (returns bytearray)
    byte_data = eeprom[start_addr:start_addr + 4]
    
    # Unpack bytes back to integer
    retrieved_value = struct.unpack('<i', byte_data)[0]
    retrieved_integers.append(retrieved_value)
    
    print(f"Read integer {retrieved_value} from EEPROM at address {start_addr}")

print(f"\nRetrieved integers: {retrieved_integers}")
print(f"Original integers:  {integers_to_write}")
print(f"Match: {retrieved_integers == integers_to_write}")