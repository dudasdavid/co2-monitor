import ustruct
import time


class PCA9685:
    def __init__(self, i2c, address=0x40):
        self.i2c = i2c
        self.address = address
        self.reset()

    def _write(self, address, value):
        self.i2c.writeto_mem(self.address, address, bytearray([value]))

    def _read(self, address):
        return self.i2c.readfrom_mem(self.address, address, 1)[0]

    def reset(self):
        self._write(0x00, 0x00) # Mode1

    def freq(self, freq=None, osc=25000000):
        if freq is None:
            prescale = self._read(0xFE)
            return int(osc / (4096 * (prescale + 1)))

        # Compute prescale correctly
        prescale = int(round(osc / (4096 * freq) - 1))

        # Clamp to chip limits
        if prescale < 3:
            prescale = 3
        elif prescale > 255:
            prescale = 255

        old_mode = self._read(0x00)              # MODE1
        self._write(0x00, (old_mode & 0x7F) | 0x10)  # sleep=1
        self._write(0xFE, prescale)              # PRESCALE
        self._write(0x00, old_mode & ~0x10)      # sleep=0
        time.sleep_us(500)                       # let oscillator stabilize
        self._write(0x00, (old_mode & ~0x10) | 0x80 | 0x20)  # RESTART=1, AI=1

    def pwm(self, index, on=None, off=None):
        if on is None or off is None:
            data = self.i2c.readfrom_mem(self.address, 0x06 + 4 * index, 4)
            return ustruct.unpack('<HH', data)
        data = ustruct.pack('<HH', on, off)
        self.i2c.writeto_mem(self.address, 0x06 + 4 * index,  data)

    def duty(self, index, value=None, invert=False):
        if value is None:
            pwm = self.pwm(index)
            if pwm == (0, 4096):
                value = 0
            elif pwm == (4096, 0):
                value = 4095
            value = pwm[1]
            if invert:
                value = 4095 - value
            return value
        if not 0 <= value <= 4095:
            raise ValueError("Out of range")
        if invert:
            value = 4095 - value
        if value == 0:
            self.pwm(index, 0, 4096)
        elif value == 4095:
            self.pwm(index, 4096, 0)
        else:
            self.pwm(index, 0, value)
