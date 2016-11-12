from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function, unicode_literals
import Python_I2C as I2C
import time
from ctypes import c_short

def getS16(data, index):
    return c_short((data[index] << 8) + data[index + 1]).value

def getU16(data, index):
    return (data[index] << 8) + data[index + 1]

I2C_ADDR = 0x77
I2C_BUSNUM = 1

MODES = dict(
ultra_low_power = [0, 0.005],
standard = [1, 0.008],
high_resolution = [2, 0.014],
ultra_high_resolution = [3, 0.026]
)

REG_MEAS = 0xF4
REG_ID = 0xD0
REG_CALIB = 0xAA

REG_MSB = 0xF6
REG_LSB = 0xF7
REG_XLSB = 0xF8

CMD_READTEMP = 0x2E
CMD_READPRESSURE = 0x34

class BMP():
    def __init__(self, address=I2C_ADDR, busnum=I2C_BUSNUM, mode='standard'):
        self._dev = I2C.Device(address, busnum)

        self._load_calibration()

        if mode in list(MODES.keys()):
            self._mode = mode

        else:
           raise Exception('enter one of these modes %s' % (str(list(MODES.keys())))) 

    def _load_calibration(self):
        self._cal = {}

        cal = self._dev.readList(REG_CALIB, 22)

        self._cal['AC1'] = getS16(cal, 0)
        self._cal['AC2'] = getS16(cal, 2)
        self._cal['AC3'] = getS16(cal, 4)
        self._cal['AC4'] = getU16(cal, 6)
        self._cal['AC5'] = getU16(cal, 8)
        self._cal['AC6'] = getU16(cal, 10)
        self._cal['B1'] = getS16(cal, 12)
        self._cal['B2'] = getS16(cal, 14)
        self._cal['MB'] = getS16(cal, 16)
        self._cal['MC'] = getS16(cal, 18)
        self._cal['MD'] = getS16(cal, 20)

    def _read_ut(self):
        self._dev.write8(REG_MEAS, CMD_READTEMP)

        time.sleep(0.005)

        msb, lsb = self._dev.readList(REG_MSB, 2)
        
        UT = (msb << 8) + lsb

        return UT

    def _read_up(self):
        oss = MODES[self._mode][0]
        wait_time = MODES[self._mode][1]

        self._dev.write8(REG_MEAS, CMD_READPRESSURE + (oss << 6))

        time.sleep(wait_time)

        msb, lsb, xlsb = self._dev.readList(REG_MSB, 3)

        UP = ((msb << 16) + (lsb << 8) + xlsb) >> (8 - oss)

        return UP

    def read_temperature(self):
        UT = self._read_ut()
        
        X1 = ((UT - self._cal['AC6']) * self._cal['AC5']) >> 15
        X2 = (self._cal['MC'] << 11) // (X1 + self._cal['MD'])
        B5 = X1 + X2
        T = (B5 + 8) >> 4

        return round((T * 0.1), 1)

    def read_pressure(self):
        oss = MODES[self._mode][0]
        
        UT = self._read_ut()
        UP = self._read_up()

        X1 = ((UT - self._cal['AC6']) * self._cal['AC5']) >> 15
        X2 = (self._cal['MC'] << 11) // (X1 + self._cal['MD'])
        B5 = X1 + X2
        B6 = B5 - 4000
        B6 = B6 * B6 >> 12
        X1 = (self._cal['B2'] * B6) >> 11
        X2 = self._cal['AC2'] * B6 >> 11
        X3 = X1 + X2
        B3 = (((self._cal['AC1'] * 4 + X3) << oss) + 2) >> 2
        X1 = self._cal['AC3'] * B6 >> 13
        X2 = (self._cal['B1'] * B6) >> 16
        X3 = ((X1 + X2) + 2) >> 2
        B4 = (self._cal['AC4'] * (X3 + 32768)) >> 15
        B7 = (UP - B3) * (50000 >> oss)

        if B7 < 0x80000000:
            P = (B7 * 2) // B4

        else:
            P = (B7 // B4) * 2

        X1 = (P >> 8) ** 2
        X1 = (X1 * 3038) >> 16
        X2 = (-7357 * P) >> 16
        P = P + ((X1 + X2 + 3791) >> 4)

        return int(float(P) * 10) / 10

    def read_altitude(self, sealevel_pressure=101325.0):
        pressure = float(self.read_pressure())
        altitude = 44330.0 * (1.0 - pow(pressure / sealevel_pressure, (1.0/5.255)))

        return altitude

    def read_sealevel_pressure(self, altitude_m=0.0):
        pressure = float(self.read_pressure())
        sealevel_pressure = pressure / pow(1.0 - altitude_m/44330.0, 5.255)

        return sealevel_pressure
    
    def readID(self):
        chip_id, chip_version = self._dev.readList(REG_ID, 2)

        return chip_id, chip_version

