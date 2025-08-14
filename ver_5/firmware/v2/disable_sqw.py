import time
import board
import busio

i2c = busio.I2C(board.P0_11, board.P1_04)  # SCL, SDA
addr = 0x68

def w8(reg, val):
    while not i2c.try_lock():
        pass
    i2c.writeto(addr, bytes([reg, val]))
    i2c.unlock()

def r8(reg):
    while not i2c.try_lock():
        pass
    i2c.writeto(addr, bytes([reg]))  # Send register address
    result = bytearray(1)
    i2c.readfrom_into(addr, result)  # Read 1 byte
    i2c.unlock()
    return result[0]

# ---- Configure DS3231 to output interrupt instead of square wave ----

# 1) Disable square wave; enable Alarm1 interrupt; INTCN=1
ctrl = r8(0x0E)
# bits: [EOSC,BBSQW,CONV,RS2,RS1,INTCN,A2IE,A1IE]
ctrl |= 0b00000101   # INTCN=1, A1IE=1
ctrl &= 0b11100111   # (optional) zero RS bits
w8(0x0E, ctrl)

# 2) Clear any existing flags
stat = r8(0x0F)
stat &= 0b11111100   # clear A1F/A2F
w8(0x0F, stat)

# 3) Program Alarm1 to fire once per second (just for test)
#    Alarm1 regs 0x07..0x0A: sec, min, hr, day/date
#    Set all with MSB=1 (A1M*=1) to match always
for reg in (0x07, 0x08, 0x09, 0x0A):
    w8(reg, 0x80)  # A1M*=1

print("INT/SQW should now go LOW and stay low until A1F is cleared.")

# 4) Clear alarm flag after a couple seconds to release line HIGH
time.sleep(2)
stat = r8(0x0F)
w8(0x0F, stat & 0b11111101)  # clear A1F only

