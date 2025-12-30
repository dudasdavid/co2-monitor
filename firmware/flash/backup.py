import uos
import machine
from machine import Pin, I2C, RTC
import time
import pyb
try:
    from drivers import ds3231 as ds3231_driver
except:
    print("Cannot import RTC driver!!!")

def make_timestamp():
    t = time.localtime()
    return "{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}".format(
        t[0], t[1], t[2], t[3], t[4], t[5]
    )

def copy_file(src, dst):
    with open(src, "rb") as fsrc:
        with open(dst, "wb") as fdst:
            while True:
                buf = fsrc.read(1024)
                if not buf:
                    break
                fdst.write(buf)

def copy_recursive(src_dir, dst_dir):
    for name in uos.listdir(src_dir):
        src_path = src_dir + "/" + name
        dst_path = dst_dir + "/" + name

        try:
            stat = uos.stat(src_path)
            mode = stat[0]

            if mode & 0o40000:  
                # directory
                try:
                    uos.mkdir(dst_path)
                except OSError:
                    pass
                copy_recursive(src_path, dst_path)
            else:
                # file
                copy_file(src_path, dst_path)

        except Exception as e:
            print("Error copying", src_path, "->", dst_path, ":", e)

def is_sd_mounted(path="/sd"):
    try:
        uos.statvfs(path)
        return True
    except OSError:
        return False

def main():
    # --- 0. Cync MCU timestamp from RTC (or at least try to do so...) ---
    # I2C1 uses PB8=D15 (SCL) / PB9=D14 (SDA) on STM32F746 builds
    i2c1=I2C(1, freq=100000)
    print("i2c1 scan result:", i2c1.scan())
    try:
        # Initialize the DS3231 RTC
        ds3231 = ds3231_driver.DS3231(i2c1)
        rtc_datetime = ds3231.datetime()
        print("RTC datetime at init:", rtc_datetime)
        
        # Initialize MCU's RTC HW
        rtc_mcu = RTC()
        rtc_mcu.datetime(rtc_datetime)
        print("MCU RTC was initialized to:", time.localtime())
        
    except Exception as e:
        print("MCU timestamp couldn't be updated:", e)
    
    
    # --- 1. Prepare SD card ---
    # NOTE: You must have already created sd = machine.SDCard() and mounted it once!
    if not is_sd_mounted("/sd"):
        import pyb
        sd = pyb.SDCard()
        sd.info()
        uos.mount(sd, '/sd')
        try:
            uos.mount(sd, "/sd")
        except OSError:
            # Already mounted
            pass
    else:
        print("SD card is already mounted")

    # Create /sd/backup/ directory if it doesn't exist
    try:
        uos.mkdir("/sd/backup")
    except OSError:
        pass

    # --- 2. Create timestamped folder ---
    folder = "/sd/backup/" + make_timestamp()
    uos.mkdir(folder)

    print("Backing up /flash →", folder)

    # --- 3. Copy everything ---
    copy_recursive("/flash", folder)

    print("Backup complete!")

main()