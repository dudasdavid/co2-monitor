import uasyncio as asyncio
import time
from machine import Pin, I2C, RTC
from logger import Logger
from drivers import veml7700 as veml7700_driver
from drivers import ens160 as ens160_driver
from drivers import ahtx0 as athx0_driver
from drivers import scd4x as scd4x_driver
from drivers import ds3231 as ds3231_driver
from drivers import bmp280 as bmp280_driver

# ---- Global variables ----
import shared_variables as var

log = Logger("i2c", debug_enabled=False)

def is_time_diff_over_threshold(ntp_time, rtc_time, threshold_seconds=60):
    """
    ntp_time and rtc_time are tuples like:
    (year, month, day, weekday, hour, minute, second, subsecond)

    Returns True if the absolute difference is > threshold_seconds (default 60s),
    otherwise False. If either is None or invalid, logs a warning and returns False.
    """
    if ntp_time is None or rtc_time is None:
        log.warning("NTP or RTC time is None, cannot compare.")
        return False

    try:
        # Unpack only the fields we actually need
        ny, nmo, nd, _, nh, nmin, ns, _ = ntp_time
        ry, rmo, rd, _, rh, rmin, rs, _ = rtc_time

        # Build time tuples compatible with time.mktime:
        # (year, month, mday, hour, minute, second, weekday, yearday)
        # weekday & yearday can be 0, they are usually ignored by mktime.
        ntp_struct = (ny, nmo, nd, nh, nmin, ns, 0, 0)
        rtc_struct = (ry, rmo, rd, rh, rmin, rs, 0, 0)

        ntp_seconds = time.mktime(ntp_struct)
        rtc_seconds = time.mktime(rtc_struct)

        diff = abs(ntp_seconds - rtc_seconds)
        return diff > threshold_seconds

    except Exception as e:
        log.warning("Failed to compare times:", ntp_time, rtc_time, "| Error:", e)
        return False

async def i2c_task(period = 1.0):
    #Init
    
    # I2C1 uses PB8=D15 (SCL) / PB9=D14 (SDA) on STM32F746 builds
    i2c1=I2C(1, freq=100000)
    log.info("Scan result:", i2c1.scan())
    
    # Initialize the VEML7700 Lux sensor
    veml7700_sensor = veml7700_driver.VEML7700(address=0x10, i2c=i2c1, it=400, gain=1/8)

    # Initialize the ENS160 AQI sensor
    ens160_sensor = ens160_driver.ENS160(i2c1)
    # Initialize the AHT21 temperature sensor
    aht21_sensor = athx0_driver.AHT20(i2c1)

    # Initialize the DS3231 RTC
    ds3231 = ds3231_driver.DS3231(i2c1)
    rtc_datetime = ds3231.datetime()
    log.info("[DS3231] RTC datetime at init:", rtc_datetime)
    
    # Initialize MCU's RTC HW
    rtc_mcu = RTC()
    rtc_mcu.datetime(rtc_datetime)
    log.info("MCU RTC was initialized to:", time.localtime())

    # Initialize the BMP280 Pressure sensor
    bmp280 = bmp280_driver.BMP280(i2c1)
    bmp280.use_case(bmp280_driver.BMP280_CASE_INDOOR)
    bmp280.oversample(bmp280_driver.BMP280_OS_STANDARD)
    bmp280.temp_os    = bmp280_driver.BMP280_TEMP_OS_1
    bmp280.press_os   = bmp280_driver.BMP280_PRES_OS_1
    bmp280.standby    = bmp280_driver.BMP280_STANDBY_250
    bmp280.iir        = bmp280_driver.BMP280_IIR_FILTER_4
    bmp280.power_mode = bmp280_driver.BMP280_POWER_NORMAL
    #bmp280.normal_measure()
    #bmp280.in_normal_mode()
    time.sleep(0.1)
    init_pressure = bmp280.pressure
    
    # Initialize the SCD4X CO2 sensor
    scd4x = scd4x_driver.SCD4X(i2c1)
    scd4x.set_ambient_pressure(init_pressure)
    log.info("[SCD41] pressure initialized to", init_pressure, "hPa")
    scd4x.start_periodic_measurement()


    #Run
    while True:
        lux = veml7700_sensor.read_lux()
        log.debug("[VEML7700] Lux", lux)
        var.sensor_data.lux_veml7700 = lux if lux is not None else 0
        
        temp = aht21_sensor.temperature + var.aht21_temp_offset
        rh = aht21_sensor.relative_humidity
        log.debug("[AHT21] temperature:", temp)
        log.debug("[AHT21] humidity:", rh)
        var.sensor_data.temp_aht21 = temp if temp is not None else 0
        var.sensor_data.humidity_aht21 = rh if rh is not None else 0
        
        aqi, tvoc, eco2, temp, rh, eco2_rating, tvoc_rating = ens160_sensor.read_air_quality()

        log.debug("[ENS160] temperature:", temp)
        log.debug("[ENS160] humidity:", rh)
        log.debug("[ENS160] AQI:", aqi)
        log.debug("[ENS160] TVOC:", tvoc, "-", tvoc_rating)
        log.debug("[ENS160] eCO2:", eco2, "-", eco2_rating)
        
        var.sensor_data.temp_ens160 = temp if temp is not None else 0
        var.sensor_data.humidity_ens160 = rh if rh is not None else 0
        var.sensor_data.aqi_ens160 = aqi if aqi is not None else 0
        var.sensor_data.tvoc_ens160 = tvoc if tvoc is not None else 0
        var.sensor_data.tvoc_rating_ens160 = tvoc_rating if tvoc_rating is not None else "N/A"
        var.sensor_data.eco2_ens160 = eco2 if eco2 is not None else 0
        var.sensor_data.eco2_rating_ens160 = eco2_rating if eco2_rating is not None else "N/A"
        
        co2 = scd4x.co2
        temp = scd4x.temperature
        rh = scd4x.relative_humidity
        log.debug("[SCD41] CO2:", co2)
        log.debug("[SCD41] temperature:", temp)
        log.debug("[SCD41] humidity:", rh)
        var.sensor_data.co2_scd41 = co2 if co2 is not None else 0
        var.sensor_data.temp_scd41 = temp if temp is not None else 0
        var.sensor_data.humidity_scd41 = rh if rh is not None else 0
        
        var.system_data.time_rtc = ds3231.datetime()
        log.debug("[DS3231] RTC datetime:", var.system_data.time_rtc)
        
        if is_time_diff_over_threshold(var.system_data.time_ntp, var.system_data.time_rtc, 60):
            log.warning("[DS3231] RTC time needs to be updated from NTP time!", var.system_data.time_ntp)
            ds3231.datetime(var.system_data.time_ntp)
        
        pressure = bmp280.pressure
        temp = bmp280.temperature
        log.debug("[BMP280] pressure:", pressure)
        log.debug("[BMP280] temperature:", temp)
        var.sensor_data.pressure_bmp280 = pressure if pressure is not None else 0
        var.sensor_data.temp_bmp280 = temp if temp is not None else 0
        
        await asyncio.sleep(period)
