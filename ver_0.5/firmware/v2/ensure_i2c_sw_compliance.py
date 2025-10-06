import board
import busio

i2c = busio.I2C(board.P0_11, board.P1_04)  # SCL, SDA
addr = 0x68  # DS3231 I2C address

CTRL_REG = 0x0E

def read_byte(reg):
    while not i2c.try_lock():
        pass
    i2c.writeto(addr, bytes([reg]))
    result = bytearray(1)
    i2c.readfrom_into(addr, result)
    i2c.unlock()
    return result[0]

def write_byte(reg, val):
    while not i2c.try_lock():
        pass
    i2c.writeto(addr, bytes([reg, val]))
    i2c.unlock()

# Read current control register value
ctrl = read_byte(CTRL_REG)
print("Current CTRL reg: 0x{:02X}".format(ctrl))

# Bits: [EOSC, BBSQW, CONV, RS2, RS1, INTCN, A2IE, A1IE]
BBSQW = (ctrl >> 6) & 1
INTCN  = (ctrl >> 2) & 1
print("BBSQW =", BBSQW, "INTCN =", INTCN)

# Ensure BBSQW = 0, INTCN = 1
new_ctrl = (ctrl & ~(1 << 6)) | (1 << 2)
if new_ctrl != ctrl:
    print("Updating CTRL reg to 0x{:02X}".format(new_ctrl))
    write_byte(CTRL_REG, new_ctrl)
else:
    print("CTRL reg already set correctly.")

