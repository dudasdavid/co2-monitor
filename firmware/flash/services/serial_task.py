import uasyncio as asyncio
from machine import UART
import time
from logger import Logger

# ---- Global variables ----
import shared_variables as var

log = Logger("uart", debug_enabled=True)

def parse_time_string(s: bytes, hours_offset=0):
    """
    Parse a UART time string like:
        b'TIME:2025,11,19,3,19,16,11,0\\r\\n'
    Returns a tuple of integers:
        (year, month, day, weekday, hour, minute, second, subsecond)
    Applies hours_offset before returning.
    On parse error: prints a warning and returns None.
    """
    try:
        # decode bytes → strip \r\n → string
        text = s.decode().strip()

        # must start with TIME:
        if not text.startswith("TIME:"):
            raise ValueError("Missing TIME prefix")

        # remove prefix
        text = text[5:]

        # split by commas
        parts = text.split(",")

        # expect exactly 8 elements
        if len(parts) != 8:
            raise ValueError("Incorrect number of fields")

        # convert to integers
        y, mo, d, wd, h, mi, sec, sub = (int(x) for x in parts)

        # Build a tuple for mktime (weekday & yearday ignored)
        t = (y, mo, d, h, mi, sec, 0, 0)

        # Convert → shift hours → back to tuple
        base_seconds = time.mktime(t)
        shifted_seconds = base_seconds + hours_offset * 3600

        # Convert back to localtime tuple
        newt = time.localtime(shifted_seconds)

        # Reconstruct 8-field tuple (weekday and subsecond kept as provided)
        corrected = (
            newt[0],  # year
            newt[1],  # month
            newt[2],  # day
            newt[6] + 1,  # weekday: convert 0=Mon → 1..7
            newt[3],  # hour
            newt[4],  # minute
            newt[5],  # second
            sub       # keep original subsecond
        )

        return corrected

    except Exception as e:
        log.warning("Cannot parse TIME string:", s, "| Error:", e)
        return None

async def serial_task(period = 1.0):
    #Init
    uart6 = UART(6, baudrate=115200, bits=8, parity=None, stop=1, timeout=1000)

    #Run
    while True:
        
        _ = uart6.read(uart6.any() or 0)  # dump whatever is there
        await asyncio.sleep(0.1)
        
        uart6.write(b'STATUS?\n')
        await asyncio.sleep(0.1)
        connection = uart6.readline()
        log.debug("STATUS?", connection)
        
        if connection is not None:
            if connection[0:7] == b'STATUS:':
                var.system_data.status_wifi = str(connection)[9:-5].replace(" ", " | ")
            else:
                var.system_data.status_wifi = connection
        else:
            var.system_data.status_wifi = "ESP8266 is OFFLINE"
            
        
        uart6.write(b'TIME?\n')
        await asyncio.sleep(0.1)
        ntp_time_str = uart6.readline()
        log.debug("TIME?", ntp_time_str)
        var.system_data.time_ntp = parse_time_string(ntp_time_str, var.time_offset_ntp)
        log.debug(var.system_data.time_ntp)
        
        uart6.write(b'TEMP:' + str(var.sensor_data.temp_aht21) + ',' + str(var.sensor_data.humidity_aht21) + '\n')
        #error = uart6.readline()
        #if error is not None:
        #    log.warning(error)
        uart6.write(b'AQI:' + str(var.sensor_data.aqi_ens160) + ',1,2,' + str(var.sensor_data.tvoc_ens160) + '\n') # PM2_5 and PM10 is 1 and 2 as placeholder
        #error = uart6.readline()
        #if error is not None:
        #    log.warning(error)
        uart6.write(b'CO2:' + str(var.sensor_data.co2_scd41) + ',' + str(var.scd41_co2_peak_ppm) + ',' + str(var.scd41_co2_detected) + '\n')
        #error = uart6.readline()
        #if error is not None:
        #    log.warning(error)
        uart6.write(b'LUX:' + str(var.sensor_data.lux_veml7700) + '\n')
        #error = uart6.readline()
        #if error is not None:
        #    log.warning(error)
        
        uart6.write(b'PWM:' + str(var.system_data.bl_duty_percent) + '\n')
        await asyncio.sleep(0.1)
        feedback = uart6.readline()
        log.debug(feedback)
        
        var.system_data.serial_task_timestamp = time.time()
        
        await asyncio.sleep(period)

