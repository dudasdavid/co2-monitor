import uasyncio as asyncio
from logger import Logger
import time

# ---- Global variables ----
import shared_variables as var
 
async def fake_ap_activation_task(period_pre = 10, period_post = 120.0):
    #Init
    log = Logger("ap_req", debug_enabled=True)

    #Run
    while True:
        await asyncio.sleep(period_pre)
        var.ap_request = not var.ap_request
        log.debug("AP request changed to:", var.ap_request)
        await asyncio.sleep(period_post)
                
        


