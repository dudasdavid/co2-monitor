import uasyncio as asyncio
from machine import UART, Pin
from logger import Logger
from drivers import ld2410 as ld2410_driver

# ---- Global variables ----
import shared_variables as var

async def serial_task(period = 1.0):
    #Init
    log = Logger("uart", debug_enabled=False)
    
    uart = UART(
        0,
        baudrate=256000,
        tx=Pin(0),
        rx=Pin(1)
    )
    
    ld2410 = ld2410_driver.LD2410(uart)
    #ld2410.set_basic_config(8,8,presence_timeout=5)
    #ld2410.set_resolution(75)

    #Run
    while True:
        log.debug("Task is running")
        
        ld2410.read()
        
        log.debug("mmWave detection:", ld2410.detected)
        var.mm_wave_detected = ld2410.detected
        
        await asyncio.sleep(period)