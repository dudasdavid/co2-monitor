import sys
import uasyncio as asyncio
import pyb
import os
import sys
import time
from logger import Logger

log = Logger("boot", debug_enabled=False)

def is_sd_mounted(path="/sd"):
    try:
        os.statvfs(path)
        return True
    except OSError:
        return False

def mount_sd_card():
    # ----- Mount SD card -----
    
    if not is_sd_mounted("/sd"):
        try:
            # Mount SD card
            sd = pyb.SDCard()
            sd.info()
            os.mount(sd, '/sd')
            sd_mounted = True
            log.info("SD card mounted at /sd")
            
        except Exception as e:
            log.error("Failed to mount SD card:", e)
            log.warning("Recovery with SD card power off")
            sd.power(False)
            time.sleep(1)
            sd.power(True)
            time.sleep(1)
            os.mount(sd, '/sd')
            sd_mounted = True
            log.info("SD card mounted at /sd")
    else:
        log.info("SD card already mounted")
    
    try:
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
       
    except Exception as e:
        log.error("Failed to read SD card:", e)

log.info("Starting up...")

mount_sd_card()

# --- add your module folder ---
if "/sd/python" not in sys.path:
    sys.path.append("/sd/python")

import main_staging

try:
    asyncio.run(main_staging.main())
except Exception as e:
    # Print error so you can see it in the Thonny shell
    print("FATAL ERROR in main:", e)
    sys.print_exception(e)
    
