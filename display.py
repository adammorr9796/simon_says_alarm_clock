# Author: Adam Morrison
#   Date: 19-Feb-2022

# For Adafruit 7-Segment LED FeatherWings I2C backpack
# and Raspberry Pi Zero W
# Pin Connections:
#    RPI    FeatherwingBkpk
#    1   => 3.3V
#    3   => SDA
#    5   => SCL
#    9   => GND

import smbus
import time

# bitmaps - each bit maps to a,b,c,d,e,f,g,dot connections on single segment
# place in array corresponds to number to display (i.e. bmaps[0] displays a zero, etc.)
bmaps = [
    0b00111111,
    0b00000110,
    0b01011011,
    0b01001111,
    0b01100110,
    0b01101101,
    0b01111101,
    0b00000111,
    0b01111111,
    0b01101111
]

digit_addr = [0x00, 0x02, 0x06, 0x08]
COL_ADDR = 0x04
COL_ON = 0b00000010
COL_OFF = 0b00000000
DECIMAL = 0b10000000

BKPK_I2C_ADDR = 0x70
RPI_I2C_BUS = 1

class Display:
    def __init__(self, address, bus):
        self.addr = address
        self.i2c_bus = smbus.SMBus(bus)

    def setup(self):
        self.i2c_bus.write_byte(self.addr, 0x21) # internal clk enable
        self.i2c_bus.write_byte(self.addr, 0xA0) # row/int set
        self.i2c_bus.write_byte(self.addr, 0x81) # display on
        self.i2c_bus.write_byte(self.addr, 0xEF) # set brightness to max (15 == 0xF)

    def set_blink(self, rate):
        if (rate < 0 or rate > 3):
            return
        else:
            self.i2c_bus.write_byte(self.addr, 0x81 | (rate << 1)) # accding to datasheet: 0 == OFF, 1 = 2Hz, 2 == 1Hz, 3 == 0.5Hz

    def write_digit(self, digit, num, decimal):
        if (digit < 0 or digit > 3 or num < 0 or num > 9):
            return
        if (decimal):
            self.i2c_bus.write_byte_data(self.addr, digit_addr[digit], bmaps[num] | DECIMAL)
        else:
            self.i2c_bus.write_byte_data(self.addr, digit_addr[digit], bmaps[num])

    def write_colon(self, enable):
        if (enable):
            self.i2c_bus.write_byte_data(self.addr, COL_ADDR, COL_ON)
        else:
            self.i2c_bus.write_byte_data(self.addr, COL_ADDR, COL_OFF)

if __name__ == "__main__":
    print("TESTING SevenSegmentBackpack")

    display = Display(BKPK_I2C_ADDR, RPI_I2C_BUS);

    display.setup()

    display.write_colon(True)
    time.sleep(1)
    display.write_colon(False)
    time.sleep(1)
    display.write_colon(True)
    time.sleep(1)

    for i in range(0,30):
            display.write_digit(i%4, i%10)
            time.sleep(0.5)
