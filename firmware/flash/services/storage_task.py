import uasyncio as asyncio
import os
import pyb
from logger import Logger
import time

# ---- Global variables ----
import shared_variables as var


log = Logger("stor", debug_enabled=False)

CSV_HEADER = "timestamp,temperature,humidity,co2,tvoc,aqi,pm10,pm2_5,pressure,lux\n"

# ---- Helpers ----

def localtime_with_offset(offset_sec=var.TZ_OFFSET):
    # get current UTC epoch
    utc_epoch = time.time()
    
    # apply offset
    local_epoch = utc_epoch + offset_sec
    
    # convert back to tuple
    return time.localtime(local_epoch)

def _format_timestamp(t):
    """
    t: (year, month, day, weekday, hour, minute, second, subsecond)
    returns: 'YYYY-MM-DD HH:MM:SS'
    """
    y, mo, d, _, hh, mm, ss, _ = t
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        y, mo, d, hh, mm, ss
    )

def _parse_timestamp(s):
    """
    'YYYY-MM-DD HH:MM:SS' -> (year, month, day, hour, minute, second)
    time.mktime expects the following format: time.mktime((2025,11,25,20,30,57,0,0))
    last 2 are dummy (0), mktime ignores them in MicroPython.
    """
    try:
        date_str, time_str = s.split(" ")
        y, mo, d = [int(x) for x in date_str.split("-")]
        hh, mm, ss = [int(x) for x in time_str.split(":")]
        return (y, mo, d, hh, mm, ss, 0, 0)
    except:
        return None
    
def _safe(value, default=0):
    """Replace None with default so formatting doesn't crash."""
    return value if value is not None else default

def _file_exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def _is_valid_csv(path):
    try:
        with open(path, "r") as f:
            first = f.readline()
            return first == CSV_HEADER
    except OSError:
        return False


def _safe_remove(path):
    try:
        os.remove(path)
    except OSError:
        pass


def _safe_rename(src, dst):
    try:
        _safe_remove(dst)
        os.rename(src, dst)
        return True
    except OSError:
        return False


def _ensure_log_file(path, log):
    
    CSV_EXT = ".csv"
    TMP_EXT = ".tmp"
    BAK_EXT = ".bak"
    
    csv = path + CSV_EXT
    tmp = path + TMP_EXT
    bak = path + BAK_EXT

    # 1) Always remove temp file (never trusted)
    if _file_exists(tmp):
        _safe_remove(tmp)
        log.info("Removed temp log file:", tmp)

    csv_ok = _file_exists(csv) and _is_valid_csv(csv)

    # 2) If CSV is valid → cleanup backups and return
    if csv_ok:
        if _file_exists(bak):
            _safe_remove(bak)
            log.info("Removed backup log file:", bak)
        else:
            log.info("There is no .bak file to be removed")
        return
    else:
        log.error("CSV exist:", _file_exists(csv), "CSV valid:", _is_valid_csv(csv))

    # 3) CSV missing or invalid → try restore from backup
    if _file_exists(bak) and _is_valid_csv(bak):
        if _safe_rename(bak, csv):
            log.warning("Restored log file from backup:", csv)
            return
    else:
        log.warning("CSV is missing and ther is no backup to restore")

    # 4) Nothing usable → create fresh CSV with header
    try:
        with open(csv, "w") as f:
            f.write(CSV_HEADER)
        log.warning("Created new log file with header:", csv)
    except Exception as e:
        log.error("Failed to create log file:", csv, e)

def is_sd_mounted(path="/sd"):
    try:
        os.statvfs(path)
        return True
    except OSError:
        return False

def sd_card_recovery():

    if is_sd_mounted("/sd"):
        os.umount("/sd")

    sd = pyb.SDCard()
    sd.power(False)
    time.sleep(1)
    sd.power(True)
    time.sleep(1)
    try:
        os.mount(sd, '/sd')
        log.warning("SD card recovery was done!")
        var.system_data.status_sd = "Online"
    except Exception as e:
        log.error("SD card recovery failed!", e)
        var.system_data.status_sd = "Offline"

async def _append_sensor_row(path, limit_rows, yield_every=20):
    """
    Append one sensor row and trim to last `limit_rows` data lines.
    """
    # Build CSV line
    timestamp = localtime_with_offset()
    ts_str = _format_timestamp(timestamp)

    temp = _safe(var.sensor_data.temp_aht21)
    hum = _safe(var.sensor_data.humidity_aht21)
    co2 = int(_safe(var.sensor_data.co2_scd41))
    tvoc = int(_safe(var.sensor_data.tvoc_ens160))
    aqi = int(_safe(var.sensor_data.aqi_ens160))
    pm10 = _safe(var.sensor_data.pm10_filtered_sps30)
    pm2_5 = _safe(var.sensor_data.pm2_5_filtered_sps30)
    pressure = _safe(var.sensor_data.pressure_bmp280)
    lux = _safe(var.sensor_data.lux_veml7700)

    # Format as strings (adjust precision as you like)
    row = "{},{:.2f},{:.2f},{:d},{:d},{:d},{:.2f},{:.2f},{:.2f},{:.2f}\n".format(
        ts_str,
        temp,
        hum,
        co2,
        tvoc,
        aqi,
        pm10,
        pm2_5,
        pressure,
        lux,
    )

    try:
        # Read all lines
        try:
            f = open(path + ".csv", "r")
            lines = f.readlines()
            f.close()
        except OSError:
            # If file doesn't exist for some reason, recreate with header
            lines = []
            header = "timestamp,temperature,humidity,co2,tvoc,aqi,pm10,pm2_5,pressure,lux\n"
            lines.append(header)
            log.error("File doesn't exist or error during reading, recreate with default header!")

        if not lines:
            header = "timestamp,temperature,humidity,co2,tvoc,aqi,pm10,pm2_5,pressure,lux\n"
            data_lines = []
            log.error("File doesn't exist or empty, recreate with default header!")
        else:
            header = lines[0]
            data_lines = lines[1:]

        data_lines.append(row)

        # Keep only newest `limit_rows` data lines
        log.info("Log length:", len(data_lines))
        if len(data_lines) > limit_rows:
            data_lines = data_lines[-limit_rows:]
            log.warning("Log length is longer than", limit_rows, ", log size was decreased to", len(data_lines))

        # Write everything back
        line_counter = 0
        f = open(path + ".tmp", "w")
        f.write(header)
        for l in data_lines:
            f.write(l)
            
            line_counter += 1
            if line_counter % yield_every == 0:
                await asyncio.sleep_ms(10)

        f.close()

        log.debug("Log row created, total rows:", len(data_lines))
        
        os.rename(path + ".csv", path + ".bak")
        
        log.debug("Log backup done")
        
        os.rename(path + ".tmp", path + ".csv")
        
        log.debug("New log saved")
        
        os.remove(path + ".bak")
        
        log.debug("Backup log deleted")
        
    except Exception as e:
        log.error("Failed to append sensor row:", e)
        
        sd_card_recovery()

async def _load_co2_history_from_log(path, yield_every=10):
    """
    Read /sd/sensor_logs.csv and rebuild var.scd41_co2_history
    from all entries in the last 24 hours.

    Each entry is just one CO2 value, in chronological order.
    """
    try:
        f = open(path + ".csv", "r")
    except OSError:
        log.warning("No log file found to restore CO2 history from:", path + ".csv")
        return

    try:
        # Skip header
        header = f.readline()
        if not header:
            log.warning("Log file empty, history not restored")
            return

        now_tuple = localtime_with_offset()
        log.debug("RTC timestamp:", now_tuple)
        
        try:
            now_ts = time.mktime(now_tuple)
        except Exception as e:
            log.error("mktime not available / failed, cannot restore history:", e)
            return

        one_day = 24 * 60 * 60
        min_ts = now_ts - one_day

        entries = []  # list of (ts_seconds, co2_int)
        line_counter = 0

        while True:
            line = f.readline()
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            parts = line.split(",")
            if len(parts) < 5:
                continue

            # Yield here during file reading to make sure other asyncio tasks can run
            line_counter += 1
            if line_counter % yield_every == 0:
                await asyncio.sleep_ms(50)

            ts_str = parts[0]      # 'YYYY-MM-DD HH:MM:SS'
            co2_str = parts[3]     # co2 column

            ts_tuple = _parse_timestamp(ts_str)
            #log.debug("Log timestamp:", ts_tuple)
            if ts_tuple is None:
                continue

            try:
                ts = time.mktime(ts_tuple)
            except:
                continue

            # Only keep last 24h
            if ts < min_ts or ts > now_ts:
                continue

            try:
                co2 = int(float(co2_str))
            except Exception:
                continue

            entries.append((ts, co2))

        if not entries:
            log.warning("No recent entries (last 24h) for CO2 history")
            return

        # Ensure chronological order
        entries.sort(key=lambda x: x[0])

        # Build simple list of co2 values
        history = [co2 for _, co2 in entries]

        # Respect max history length if defined
        max_len = getattr(var, "CO2_HISTORY_MAX", None)
        if max_len is not None and len(history) > max_len:
            history = history[-max_len:]

        var.scd41_co2_history = history
        log.info("Restored CO2 history from log, length:", len(history))
        
    finally:
        f.close()

async def storage_task(period = 1.0):
    #Init
    # Get file system stats
    try:
        stats = os.statvfs('/flash')

        block_size = stats[0]
        total_blocks = stats[2]
        free_blocks = stats[3]

        total_space = block_size * total_blocks
        free_space = block_size * free_blocks
        used_space = total_space - free_space

        log.info("/flash total space:", total_space / 1024, "kB")
        log.info("/flash used space:", used_space / 1024, "kB")
        log.info("/flash free space:", free_space / 1024, "kB")
        
        var.system_data.total_space_flash = total_space / 1024
        var.system_data.used_space_flash = used_space / 1024

    except Exception as e:
        var.system_data.total_space_flash = 0
        var.system_data.used_space_flash = 0
        log.error("Failed to read /flash stats:", e)
        

    # ----- Mount SD card -----
    sd_mounted = False
    try:
        # Mount SD card
        if not is_sd_mounted("/sd"):
            sd = pyb.SDCard()
            sd.info()
            os.mount(sd, "/sd")
            log.info("SD card mounted at /sd")
        else:
            log.info("SD card already mounted")

        sd_mounted = True

        # Get file system stats
        stats = os.statvfs('/sd')

        block_size = stats[0]
        total_blocks = stats[2]
        free_blocks = stats[3]

        total_space = block_size * total_blocks
        free_space = block_size * free_blocks
        used_space = total_space - free_space

        log.info("/sd total space:", total_space / 1024 / 1024, "MB")
        log.info("/sd used space:", used_space / 1024 / 1024, "MB")
        log.info("/sd free space:", free_space / 1024 / 1024, "MB")

        var.system_data.total_space_sd = total_space / 1024 / 1024
        var.system_data.used_space_sd = used_space / 1024 / 1024
        
        var.system_data.status_sd = "Online"
        
    except Exception as e:
        var.system_data.status_sd = "Offline"
        var.system_data.total_space_sd = 0
        var.system_data.used_space_sd = 0
        log.error("Failed to mount SD card:", e)
        
        sd_card_recovery()
        
        if is_sd_mounted("/sd"):
            sd_mounted = True


    log_file_path = "/sd/sensor_logs"
    if sd_mounted:
        _ensure_log_file(log_file_path, log)
        await _load_co2_history_from_log(log_file_path)
    else:
        log.error("SD card is not mounted by storage task:", e)

    var.history_loaded = True

    # We want 7 days * 24h * 12 samples/h (5 min) = 2016 rows
    MAX_ROWS = 7 * 24 * 12   # data rows (excluding header)

    # Accumulator for 5-minute interval
    save_interval_s = 5 * 60  # 300 seconds
    elapsed = 0.0

    #Run
    while True:
        #log.debug("Task is running")      

        elapsed += period
        if elapsed >= save_interval_s:
            elapsed = 0.0
            await _append_sensor_row(log_file_path, MAX_ROWS)

        var.system_data.storage_task_timestamp = time.time()

        await asyncio.sleep(period)
