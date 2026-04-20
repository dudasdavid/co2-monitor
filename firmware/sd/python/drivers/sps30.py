import time

CMD_FIRMWARE_VERSION = [0xD1, 0x00]
CMD_PRODUCT_TYPE = [0xD0, 0x02]
CMD_SERIAL_NUMBER = [0xD0, 0x33]
CMD_READ_STATUS_REGISTER = [0xD2, 0x06]
CMD_START_FAN_CLEANING = [0x56, 0x07]
CMD_AUTO_CLEANING_INTERVAL = [0x80, 0x04]
CMD_START_MEASUREMENT = [0x00, 0x10]
CMD_STOP_MEASUREMENT = [0x01, 0x04]
CMD_READ_MEASURED_VALUES = [0x03, 0x00]

NBYTES_FIRMWARE_VERSION = 3
NBYTES_PRODUCT_TYPE = 12
NBYTES_SERIAL_NUMBER = 48
NBYTES_READ_STATUS_REGISTER = 6
NBYTES_AUTO_CLEANING_INTERVAL = 6
NBYTES_MEASURED_VALUES_FLOAT = 60

# Packet size including checksum byte [data1, data2, checksum]
PACKET_SIZE = 3
# Size of each measurement data packet (PMx) including checksum bytes, in bytes
SIZE_FLOAT = 6  # IEEE754 float
SIZE_INTEGER = 3  # unsigned 16 bit integer

class SPS30:
    def __init__(self, i2c, address=0x69):
        self.i2c = i2c
        self.address = address
        self._buffer = bytearray(70)
        self.__valid = {
            "mass_density": False,
            "particle_count": False,
            "particle_size": False,
        }

    def _read_reply(self, buff, num):
        self.i2c.readfrom_into(self.address, buff, num)

    def _send_command(self, cmd, cmd_delay=0.0):
        self.i2c.writeto(self.address, bytes(cmd))
        time.sleep(cmd_delay)

    def crc_calc(self, data: list) -> int:
        crc = 0xFF
        for i in range(2):
            crc ^= data[i]
            for _ in range(8, 0, -1):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc = crc << 1

        # The checksum only contains 8-bit,
        # so the calculated value has to be masked with 0xFF
        return crc & 0x0000FF

    def firmware_version(self) -> str | None:
        self._send_command(CMD_FIRMWARE_VERSION)
        self._read_reply(self._buffer, NBYTES_FIRMWARE_VERSION)

        if self.crc_calc(self._buffer[:2]) != self._buffer[2]:
            print("CRC mismatched")
            return None

        return ".".join(map(str, self._buffer[:2]))
    
    def product_type(self) -> str | None:
        self._send_command(CMD_PRODUCT_TYPE)
        self._read_reply(self._buffer, NBYTES_PRODUCT_TYPE)
        result = ""

        for i in range(0, NBYTES_PRODUCT_TYPE, 3):
            if self.crc_calc(self._buffer[i : i + 2]) != self._buffer[i + 2]:
                print("CRC mismatched")
                return None

            result += "".join(map(chr, self._buffer[i : i + 2]))

        return result
    
    def serial_number(self) -> str | None:
        self._send_command(CMD_SERIAL_NUMBER)
        self._read_reply(self._buffer, NBYTES_SERIAL_NUMBER)
        result = ""

        for i in range(0, NBYTES_SERIAL_NUMBER, PACKET_SIZE):
            if self.crc_calc(self._buffer[i : i + 2]) != self._buffer[i + 2]:
                print("CRC mismatched")
                return None

            result += "".join(map(chr, self._buffer[i : i + 2]))

        return result
    
    def read_status_register(self) -> dict | None:
        self._send_command(CMD_READ_STATUS_REGISTER)
        self._read_reply(self._buffer, NBYTES_READ_STATUS_REGISTER)

        status = []
        for i in range(0, NBYTES_READ_STATUS_REGISTER, PACKET_SIZE):
            if self.crc_calc(self._buffer[i : i + 2]) != self._buffer[i + 2]:
                print("CRC mismatched")
                return None

            status.extend(self._buffer[i : i + 2])

        value = (
            (status[0] << 24) |
            (status[1] << 16) |
            (status[2] << 8)  |
            status[3]
        )

        binary = "{:032b}".format(value)

        speed_status = "too high/ too low" if int(binary[10]) == 1 else "ok"
        laser_status = "out of range" if int(binary[26]) == 1 else "ok"
        fan_status = "0 rpm" if int(binary[27]) == 1 else "ok"

        return {
            "speed_status": speed_status,
            "laser_status": laser_status,
            "fan_status": fan_status,
        }
    
    def start_fan_cleaning(self) -> None:
        self._send_command(CMD_START_FAN_CLEANING)

    def read_auto_cleaning_interval(self) -> int | None:
        self._send_command(CMD_AUTO_CLEANING_INTERVAL)
        self._read_reply(self._buffer, NBYTES_AUTO_CLEANING_INTERVAL)

        interval = []
        for i in range(0, NBYTES_AUTO_CLEANING_INTERVAL, 3):
            if self.crc_calc(self._buffer[i : i + 2]) != self._buffer[i + 2]:
                print("CRC mismatched")
                return None

            interval.extend(self._buffer[i : i + 2])

        return interval[0] << 24 | interval[1] << 16 | interval[2] << 8 | interval[3]

    def write_auto_cleaning_interval_days(self, days: int) -> int | None:
        seconds = days * 86400  # 1day = 86400sec
        interval = []
        interval.append((seconds & 0xFF000000) >> 24)
        interval.append((seconds & 0x00FF0000) >> 16)
        interval.append((seconds & 0x0000FF00) >> 8)
        interval.append(seconds & 0x000000FF)
        data = CMD_AUTO_CLEANING_INTERVAL
        data.extend([interval[0], interval[1]])
        data.append(self.crc_calc(data[2:4]))
        data.extend([interval[2], interval[3]])
        data.append(self.crc_calc(data[5:7]))
        self._send_command(data)
    
    def start_measurement(self) -> None:
        data_format = {"IEEE754_float": 0x03, "unsigned_16_bit_integer": 0x05}

        data = CMD_START_MEASUREMENT
        data.extend([data_format["IEEE754_float"], 0x00])
        data.append(self.crc_calc(data[2:4]))
        self._send_command(data)


    def get_measurement(self) -> dict:
        if self.__data.empty():
            return {}

        return self.__data.get()

    def stop_measurement(self) -> None:
        self._send_command(CMD_STOP_MEASUREMENT)

    def get_measurement(self) -> dict:

        self._send_command(CMD_READ_MEASURED_VALUES)
        self._read_reply(self._buffer, NBYTES_MEASURED_VALUES_FLOAT)

        result = {
            "mass_density": self.__mass_density_measurement(self._buffer[:24]),
            "particle_count": self.__particle_count_measurement(
                self._buffer[24:54]
            ),
            "particle_size": self.__particle_size_measurement(self._buffer[54:]),
            "mass_density_unit": "ug/m3",
            "particle_count_unit": "#/cm3",
            "particle_size_unit": "um",
        }

        return result
    
    def __ieee754_number_conversion(self, data: int) -> float:
        binary = "{:032b}".format(data)

        sign = int(binary[0:1])
        exp = int(binary[1:9], 2) - 127

        divider = 0
        if exp < 0:
            divider = abs(exp)
            exp = 0

        mantissa = binary[9:]

        real = int(("1" + mantissa[:exp]), 2)
        decimal = mantissa[exp:]

        dec = 0.0
        for i in range(len(decimal)):
            dec += int(decimal[i]) / (2 ** (i + 1))

        if divider == 0:
            return round((((-1) ** (sign) * real) + dec), 3)
        else:
            return round((((-1) ** (sign) * real) + dec) / pow(2, divider), 3)

    def __mass_density_measurement(self, data: list) -> dict:
        category = ["pm1.0", "pm2.5", "pm4.0", "pm10"]

        density = {"pm1.0": 0.0, "pm2.5": 0.0, "pm4.0": 0.0, "pm10": 0.0}

        for block, (pm) in enumerate(category):
            pm_data = []
            for i in range(0, SIZE_FLOAT, PACKET_SIZE):
                offset = (block * SIZE_FLOAT) + i
                if self.crc_calc(data[offset : offset + 2]) != data[offset + 2]:
                    print("'__mass_density_measurement' CRC mismatched!"
                        + "  Data: " + data[offset : offset + 2]
                        + "  Calculated CRC: " + self.crc_calc(data[offset : offset + 2])
                        + "  Expected: " + data[offset + 2]
                    )
                    self.__valid["mass_density"] = False
                    return {}

                pm_data.extend(data[offset : offset + 2])

            density[pm] = self.__ieee754_number_conversion(
                pm_data[0] << 24 | pm_data[1] << 16 | pm_data[2] << 8 | pm_data[3]
            )

        self.__valid["mass_density"] = True

        return density

    def __particle_count_measurement(self, data: list) -> dict:
        category = ["pm0.5", "pm1.0", "pm2.5", "pm4.0", "pm10"]

        count = {"pm0.5": 0.0, "pm1.0": 0.0, "pm2.5": 0.0, "pm4.0": 0.0, "pm10": 0.0}

        for block, (pm) in enumerate(category):
            pm_data = []
            for i in range(0, SIZE_FLOAT, PACKET_SIZE):
                offset = (block * SIZE_FLOAT) + i
                if self.crc_calc(data[offset : offset + 2]) != data[offset + 2]:
                    self._warn(
                        "'__particle_count_measurement' CRC mismatched!"
                        + "  Data: " + data[offset : offset + 2]
                        + "  Calculated CRC: " + self.crc_calc(data[offset : offset + 2])
                        + "  Expected: " + data[offset + 2]
                    )

                    self.__valid["particle_count"] = False
                    return {}

                pm_data.extend(data[offset : offset + 2])

            count[pm] = self.__ieee754_number_conversion(
                pm_data[0] << 24 | pm_data[1] << 16 | pm_data[2] << 8 | pm_data[3]
            )

        self.__valid["particle_count"] = True

        return count

    def __particle_size_measurement(self, data: list) -> float:
        size = []
        for i in range(0, SIZE_FLOAT, PACKET_SIZE):
            if self.crc_calc(data[i : i + 2]) != data[i + 2]:
                self._warn(
                    "'__particle_size_measurement' CRC mismatched!"
                    + "  Data: " + data[i : i + 2]
                    + "  Calculated CRC: " + self.crc_calc(data[i : i + 2])
                    + "  Expected: " + data[i + 2]
                )

                self.__valid["particle_size"] = False
                return 0.0

            size.extend(data[i : i + 2])

        self.__valid["particle_size"] = True

        return self.__ieee754_number_conversion(
            size[0] << 24 | size[1] << 16 | size[2] << 8 | size[3]
        )