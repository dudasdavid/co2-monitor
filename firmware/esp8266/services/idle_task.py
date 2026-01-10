import uasyncio as asyncio
import gc
from logger import Logger
import time

# ---- Global variables ----
import shared_variables as var
 
async def idle_task(period = 1.0):
    #Init
    log = Logger("idle", debug_enabled=True)

    #Run
    while True:
        gc.collect()
        free = gc.mem_free()
        used = gc.mem_alloc()
        total = free + used
        
        log.debug("[MEM] total:", total/1024, "kB, free:", free/1024, " kB, used:", used/1024, "kB")
                
        await asyncio.sleep(period)

