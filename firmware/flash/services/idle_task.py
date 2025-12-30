import uasyncio as asyncio
from machine import Pin
import gc
from logger import Logger

# ---- Global variables ----
import shared_variables as var
 
async def idle_task(period = 1.0):
    #Init
    log = Logger("idle", debug_enabled=False)

    #Run
    while True:
        log.debug("Task is running")
        gc.collect()
        free = gc.mem_free()
        used = gc.mem_alloc()
        total = free + used
        
        var.system_data.total_heap = total / 1024
        var.system_data.used_heap = used / 1024
        
        log.info("[MEM] total:", total, "free:", free, "used:", used)
        
        await asyncio.sleep(period)
