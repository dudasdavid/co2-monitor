import uasyncio as asyncio
from machine import Pin
import machine
from logger import Logger
import time

# ---- Global variables ----
import shared_variables as var

log = Logger("io", debug_enabled=False)   

async def io_task(period = 0.5):
    # Init button handlers
    pin = Pin(4, Pin.IN, Pin.PULL_UP)

    #Run
    while True:
        
        pin_value = pin.value()
        if pin_value == 0:
            log.warning("Reset request arrived!")
            machine.reset()
        
        await asyncio.sleep(period)
