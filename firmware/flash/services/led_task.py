import uasyncio as asyncio
from logger import Logger
import time

# ---- Global variables ----
import shared_variables as var
 
async def led_task(period = 1.0):
    #Init
    log = Logger("led", debug_enabled=True)

    #Run
    while True:
        log.debug("Task is running")
        
        var.system_data.led_task_timestamp = time.time()
        
        await asyncio.sleep(period)
