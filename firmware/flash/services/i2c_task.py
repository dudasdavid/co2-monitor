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
from drivers import pca9685 as pca9685_driver
from drivers import drv2605 as drv2605_driver
from drivers import sps30 as sps30_driver
import math

# ---- Global variables ----
import shared_variables as var

log = Logger("i2c", debug_enabled=False)

# Haptic driver instance is shared between synchronous (init is there) and async (based on swipe events) tasks
drv2605 = None

def apply_utc_offset(ntp_time):
    
    try:
        y, mo, d, wday, h, min, s, sub = ntp_time

        # Convert to epoch
        ts = time.mktime((y, mo, d, h, min, s, 0, 0))

        # Apply offset in seconds
        ts += var.TZ_OFFSET

        # Convert back
        y, mo, d, h, mi, s, wday, yday = time.localtime(ts)

        # Return in original format
        return (y, mo, d, wday, h, mi, s, sub)
    except Exception as e:
        log.warning("Failed to unpack NTP time:", ntp_time, "| Error:", e)
        return None

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

def compensate_humidity(rh_raw: float, t_raw: float, t_cal: float) -> float:
    """
    rh_raw : raw relative humidity from sensor (%)
    t_raw  : raw (uncalibrated) temperature used by sensor (°C)
    t_cal  : calibrated / real temperature (°C)
    """

    # saturation vapor pressure (hPa)
    def esat(T):
        return 6.112 * math.exp((17.62 * T) / (243.12 + T))

    # actual vapor pressure stays constant
    e = (rh_raw / 100.0) * esat(t_raw)

    # recompute RH at corrected temperature
    rh_cal = 100.0 * e / esat(t_cal)

    # clamp to physical limits
    return max(0.0, min(100.0, rh_cal))

def ema(old, new, alpha):
    if old is None:
        return new
    return old + alpha * (new - old)

async def i2c_task(period = 1.0):
    global drv2605
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
    var.system_data.time_rtc = rtc_datetime
    log.info("[DS3231] RTC datetime at init:", rtc_datetime)
    
    # Initialize MCU's RTC HW
    rtc_mcu = RTC()
    local_time = apply_utc_offset(rtc_datetime)
    rtc_mcu.datetime(local_time)
    var.system_data.time_local = local_time
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
    
    # Initialize PCA9685 PWM driver
    pca9685 = pca9685_driver.PCA9685(i2c1)
    pca9685.freq(1000)
    pca9685.duty(0, 0)
    pca9685.duty(1, 0)
    pca9685.duty(2, 0)

    # Initialize DRV2605 haptic driver
    drv2605 = drv2605_driver.DRV2605(i2c1)
    drv2605.set_waveform(52)
    drv2605.play()                     
    #drv2605.stop()
    drv2605.set_waveform(10)

    # Initialize SPS30 PM driver
    sps30 = sps30_driver.SPS30(i2c1)
    log.info("[SPS30] Firmware version:", sps30.firmware_version())
    log.debug("[SPS30] Product type:", sps30.product_type())
    log.debug("[SPS30] Serial number:", sps30.serial_number())
    log.debug("[SPS30] Status register:", sps30.read_status_register())
    log.debug("[SPS30] Auto cleaning interval:", sps30.read_auto_cleaning_interval(), "s")
    #log.info("[SPS30] Set auto cleaning interval...")
    #sps30.write_auto_cleaning_interval_days(2)
    #await asyncio.sleep(10)
    #log.info("[SPS30] Auto cleaning interval:", sps30.read_auto_cleaning_interval(), "s")
    #await asyncio.sleep(5)
    log.debug("[SPS30] Starting measurement...")
    sps30.start_measurement()
    #await asyncio.sleep(5)
    #log.info("[SPS30] Read data...")
    #log.info("[SPS30]", sps30.get_measurement())
    
    i = -1
    #Run    
    while True:
        
        i+=1
        # Only scan devices in every 80th loop which is 8s
        if i % 80 == 0:
            devices = i2c1.scan()
            var.system_data.i2c_devices = devices
            
            # AHT21
            try:
                idx = devices.index(0x38)
                devices.pop(idx)
                var.system_data.i2c_status_aht21 = "AHT21 is online at 0x38"
            except:
                var.system_data.i2c_status_aht21 = "AHT21 is NOT found at 0x38"

            # BMP280
            try:
                idx = devices.index(0x76)
                devices.pop(idx)
                var.system_data.i2c_status_bmp280 = "BMP280 is online at 0x76"
            except:
                var.system_data.i2c_status_bmp280 = "BMP280 is NOT found at 0x76"
            
            # DS3231
            try:
                idx = devices.index(0x68)
                devices.pop(idx)
                var.system_data.i2c_status_ds3231 = "DS3231 is online at 0x68"
            except:
                var.system_data.i2c_status_ds3231 = "DS3231 is NOT found at 0x68"
            
            # ENS160
            try:
                idx = devices.index(0x53)
                devices.pop(idx)
                var.system_data.i2c_status_ens160 = "ENS160 is online at 0x53"
            except:
                var.system_data.i2c_status_ens160 = "ENS160 is NOT found at 0x53"
            
            # SCD41
            try:
                idx = devices.index(0x62)
                devices.pop(idx)
                var.system_data.i2c_status_scd41 = "SCD41 is online at 0x62"
            except:
                var.system_data.i2c_status_scd41 = "SCD41 is NOT found at 0x62"
            
            # VEML7700
            try:
                idx = devices.index(0x10)
                devices.pop(idx)
                var.system_data.i2c_status_veml7700 = "VEML7700 is online at 0x10"
            except:
                var.system_data.i2c_status_veml7700 = "VEML7700 is NOT found at 0x10"

            # DRV2605
            try:
                idx = devices.index(0x5A)
                devices.pop(idx)
                var.system_data.i2c_status_drv2605 = "DRV2605 is online at 0x5A"
            except:
                var.system_data.i2c_status_drv2605 = "DRV2605 is NOT found at 0x5A"

            # PCA9685
            try:
                idx = devices.index(0x40)
                devices.pop(idx)
                var.system_data.i2c_status_pca9685 = "PCA9685 is online at 0x40"
            except:
                var.system_data.i2c_status_pca9685 = "PCA9685 is NOT found at 0x40"
                
            # SPS30
            try:
                idx = devices.index(0x69)
                devices.pop(idx)
                var.system_data.i2c_status_sps30 = "SPS30 is online at 0x69"
            except:
                var.system_data.i2c_status_sps30 = "SPS30 is NOT found at 0x69"
                
            var.system_data.i2c_status_unknown = devices

        # Only read sensors in every 10th loop which is 1s
        if i % 10 == 0:
            ##############################################
            ########## VEML7700 light sensor #############
            ##############################################
            
            lux = veml7700_sensor.read_lux()
            #log.debug("[VEML7700] Lux", lux)
            
            if lux is not None:
                lux_cal = 3.0 * lux - 0
                var.sensor_data.lux_veml7700 = lux_cal
            else:
                var.sensor_data.lux_veml7700 = 0
            
            # Add a small sleep that even driven task can take the bus
            await asyncio.sleep_ms(50)
            
            temp = aht21_sensor.temperature + var.aht21_temp_offset
            rh = aht21_sensor.relative_humidity
            #log.debug("[AHT21] temperature:", temp)
            #log.debug("[AHT21] humidity:", rh)
            
            #var.sensor_data.temp_aht21 = temp if temp is not None else 0
            # Use temperature sensor calibration here
            if temp is not None:
                temp_cal = 1.04 * temp - 10.2
                var.sensor_data.temp_aht21 = temp_cal
            else:
                temp_cal = 0.69
                var.sensor_data.temp_aht21 = temp_cal
            
            #var.sensor_data.humidity_aht21 = rh if rh is not None else 0
            if rh is not None:
                rh_cal = compensate_humidity(rh, temp, temp_cal)
                var.sensor_data.humidity_aht21 = rh_cal
            else:
                var.sensor_data.humidity_aht21 = 0

            # Add a small sleep that even driven task can take the bus
            await asyncio.sleep_ms(50)
            
        if i % 10 == 2:
            ##############################################
            ############ ENS160 TVOC sensor ##############
            ##############################################

            aqi, tvoc, eco2, temp, rh, eco2_rating, tvoc_rating = ens160_sensor.read_air_quality()

            #log.debug("[ENS160] temperature:", temp)
            #log.debug("[ENS160] humidity:", rh)
            #log.debug("[ENS160] AQI:", aqi)
            #log.debug("[ENS160] TVOC:", tvoc, "-", tvoc_rating)
            #log.debug("[ENS160] eCO2:", eco2, "-", eco2_rating)

            if eco2 is not None:
                var.sensor_data.eco2_ens160 = eco2
                if eco2 <= 800:
                    var.sensor_data.eco2_rating_ens160 = "Excellent"
                elif eco2 <= 1000:
                    var.sensor_data.eco2_rating_ens160 = "Good"
                elif eco2 <= 1500:
                    var.sensor_data.eco2_rating_ens160 = "Moderate"
                elif eco2 <= 2000:
                    var.sensor_data.eco2_rating_ens160 = "Poor"
                elif eco2 <= 5000:
                    var.sensor_data.eco2_rating_ens160 = "Unhealthy"
                else:
                    var.sensor_data.eco2_rating_ens160 = "Hazardous"
            else:  
                var.sensor_data.eco2_ens160 = 0
                var.sensor_data.eco2_rating_ens160 = "Unknown"

            if tvoc is not None:
                var.sensor_data.tvoc_ens160 = tvoc
                if tvoc <= 150:
                    var.sensor_data.tvoc_rating_ens160 = "Excellent"
                elif tvoc <= 300:
                    var.sensor_data.tvoc_rating_ens160 = "Good"
                elif tvoc <= 500:
                    var.sensor_data.tvoc_rating_ens160 = "Moderate"
                elif tvoc <= 1000:
                    var.sensor_data.tvoc_rating_ens160 = "Poor"
                elif tvoc <= 3000:
                    var.sensor_data.tvoc_rating_ens160 = "Unhealthy"
                else:
                    var.sensor_data.tvoc_rating_ens160 = "Hazardous"
            else:  
                var.sensor_data.tvoc_ens160 = 0
                var.sensor_data.tvoc_rating_ens160 = "Unknown"
                
            if aqi is not None:
                var.sensor_data.aqi_ens160 = aqi
                if aqi == 1:
                    var.sensor_data.aqi_rating_ens160 = "Excellent"
                elif aqi == 2:
                    var.sensor_data.aqi_rating_ens160 = "Good"
                elif aqi == 3:
                    var.sensor_data.aqi_rating_ens160 = "Moderate"
                elif aqi == 4:
                    var.sensor_data.aqi_rating_ens160 = "Poor"
                elif aqi == 5:
                    var.sensor_data.aqi_rating_ens160 = "Unhealthy"
                else:
                    var.sensor_data.aqi_rating_ens160 = "Unknown"
            else:  
                var.sensor_data.aqi_ens160 = 0
                var.sensor_data.aqi_rating_ens160 = "Unknown"
            
            # Add a small sleep that even driven task can take the bus
            await asyncio.sleep_ms(50)
            
        if i % 10 == 4:
            ##############################################
            ############# SCD41 CO2 sensor ###############
            ##############################################
            
            co2 = scd4x.co2
            temp = scd4x.temperature
            rh = scd4x.relative_humidity
            #log.debug("[SCD41] CO2:", co2)
            #log.debug("[SCD41] temperature:", temp)
            #log.debug("[SCD41] humidity:", rh)
            if co2 is not None:
                var.sensor_data.co2_scd41 = co2
                if co2 <= 800:
                    var.sensor_data.co2_rating_scd41 = "Excellent"
                elif co2 <= 1000:
                    var.sensor_data.co2_rating_scd41 = "Good"
                elif co2 <= 1500:
                    var.sensor_data.co2_rating_scd41 = "Moderate"
                elif co2 <= 2000:
                    var.sensor_data.co2_rating_scd41 = "Poor"
                elif co2 <= 5000:
                    var.sensor_data.co2_rating_scd41 = "Unhealthy"
                else:
                    var.sensor_data.co2_rating_scd41 = "Hazardous"
            else:  
                var.sensor_data.co2_scd41 = 0
                var.sensor_data.co2_rating_scd41 = "Unknown"
            
            if temp is not None:
                temp_cal = 0.98 * temp - 6.8
                var.sensor_data.temp_scd41 = temp_cal
            else:
                temp_cal = 0.69
                var.sensor_data.temp_scd41 = temp_cal
            
            if rh is not None and temp is not None:
                rh_cal = compensate_humidity(rh, temp, temp_cal)
                var.sensor_data.humidity_scd41 = rh_cal
            else:
                var.sensor_data.humidity_scd41 = 0
            
            # Add a small sleep that even driven task can take the bus
            await asyncio.sleep_ms(50)
            
        if i % 10 == 5:
            ##############################################
            ########## DS3231 real time clock ############
            ##############################################
            
            var.system_data.time_rtc = ds3231.datetime()
            #log.debug("[DS3231] RTC datetime:", var.system_data.time_rtc)
            
            if is_time_diff_over_threshold(var.system_data.time_ntp, var.system_data.time_rtc, 60):
                log.warning("[DS3231] RTC time needs to be updated to NTP time!", var.system_data.time_ntp)
                ds3231.datetime(var.system_data.time_ntp)

            local_time = apply_utc_offset(var.system_data.time_rtc)
            var.system_data.time_local = local_time
            
            # Add a small sleep that even driven task can take the bus
            await asyncio.sleep_ms(50)
            
        if i % 10 == 6:
            ##############################################
            ########## BMP280 pressure sensor ############
            ##############################################
            
            pressure = bmp280.pressure
            temp = bmp280.temperature
            #log.debug("[BMP280] pressure:", pressure)
            #log.debug("[BMP280] temperature:", temp)
            var.sensor_data.pressure_bmp280 = pressure if pressure is not None else 0
            
            if temp is not None:
                temp_cal = 0.98 * temp - 5.6
                var.sensor_data.temp_bmp280 = temp_cal
            else:
                var.sensor_data.temp_bmp280 = 0
        
            # Add a small sleep that even driven task can take the bus
            await asyncio.sleep_ms(50)
        
        if i % 10 == 8:
            ##############################################
            ########## SPS30 particle sensor #############
            ##############################################
        
            # Mass density is in ug/m3
            particles = sps30.get_measurement()
            #log.debug("[SPS30] particle mass density:", particles["mass_density"])
            pm10 = int(particles["mass_density"]["pm10"])
            pm4 = int(particles["mass_density"]["pm4.0"])
            pm2_5 = int(particles["mass_density"]["pm2.5"])
            pm1 = int(particles["mass_density"]["pm1.0"])
            
            # Apply fast filtering for displaying data
            var.sensor_data.pm10_sps30  = ema(var.sensor_data.pm10_sps30,  pm10,  var.sps30_alpha_fast)
            var.sensor_data.pm4_sps30   = ema(var.sensor_data.pm4_sps30,   pm4,   var.sps30_alpha_fast)
            var.sensor_data.pm2_5_sps30 = ema(var.sensor_data.pm2_5_sps30, pm2_5, var.sps30_alpha_fast)
            var.sensor_data.pm1_sps30   = ema(var.sensor_data.pm1_sps30,   pm1,   var.sps30_alpha_fast)
            
            # Apply slow filtering for logging to MQTT
            var.sensor_data.pm10_filtered_sps30  = ema(var.sensor_data.pm10_filtered_sps30,  pm10,  var.sps30_alpha_slow)
            var.sensor_data.pm4_filtered_sps30   = ema(var.sensor_data.pm4_filtered_sps30,   pm4,   var.sps30_alpha_slow)
            var.sensor_data.pm2_5_filtered_sps30 = ema(var.sensor_data.pm2_5_filtered_sps30, pm2_5, var.sps30_alpha_slow)
            var.sensor_data.pm1_filtered_sps30   = ema(var.sensor_data.pm1_filtered_sps30,   pm1,   var.sps30_alpha_slow)
            
            if pm10 <= 20:   var.sensor_data.pm10_rating_sps30 = "Excellent"
            elif pm10 <= 50: var.sensor_data.pm10_rating_sps30 = "Good"
            elif pm10 <= 100:var.sensor_data.pm10_rating_sps30 = "Moderate"
            elif pm10 <= 200:var.sensor_data.pm10_rating_sps30 = "Poor"
            else:            var.sensor_data.pm10_rating_sps30 = "Unhealthy"
            
            if pm4 <= 5:    var.sensor_data.pm4_rating_sps30 = "Excellent"
            elif pm4 <= 15: var.sensor_data.pm4_rating_sps30 = "Good"
            elif pm4 <= 35: var.sensor_data.pm4_rating_sps30 = "Moderate"
            elif pm4 <= 75: var.sensor_data.pm4_rating_sps30 = "Poor"
            elif pm4 <= 150:var.sensor_data.pm4_rating_sps30 = "Unhealthy"
            else:           var.sensor_data.pm4_rating_sps30 = "Hazardous"
            
            if pm2_5 <= 5:    var.sensor_data.pm2_5_rating_sps30 = "Excellent"
            elif pm2_5 <= 15: var.sensor_data.pm2_5_rating_sps30 = "Good"
            elif pm2_5 <= 35: var.sensor_data.pm2_5_rating_sps30 = "Moderate"
            elif pm2_5 <= 75: var.sensor_data.pm2_5_rating_sps30 = "Poor"
            elif pm2_5 <= 150:var.sensor_data.pm2_5_rating_sps30 = "Unhealthy"
            else:             var.sensor_data.pm2_5_rating_sps30 = "Hazardous"
            
            if pm1 <= 5:   var.sensor_data.pm1_rating_sps30 = "Excellent"
            elif pm1 <= 10:var.sensor_data.pm1_rating_sps30 = "Good"
            elif pm1 <= 25:var.sensor_data.pm1_rating_sps30 = "Moderate"
            else:          var.sensor_data.pm1_rating_sps30 = "Poor"
            
            # Add a small sleep that even driven task can take the bus
            await asyncio.sleep_ms(50)
        
        ##############################################
        ### LED animation with PCA9685 PWM driver ####
        ##############################################
            
        #log.info(var.system_data.feedback_led)
        
        pca9685.duty(0, var.system_data.feedback_led[2])
        pca9685.duty(1, var.system_data.feedback_led[1])
        pca9685.duty(2, var.system_data.feedback_led[0])
        
        var.system_data.i2c_task_timestamp = time.time()
        
        await asyncio.sleep(period)

async def i2c_async_task():
    global drv2605
    
    #Init
    log = Logger("haptic", debug_enabled=True)

    #Run
    while True:
        event_type = await var.haptic_events.get()
        log.debug("Haptic event arrived:", event_type)
        if event_type == var.EVENT_FB_SWIPE_LEFT or event_type == var.EVENT_FB_SWIPE_RIGHT:
            drv2605.set_waveform(10)
        else:
            drv2605.set_waveform(52)
            
        drv2605.play()
