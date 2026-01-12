import uasyncio as asyncio
from services.networking_task import networking_task
from services.mqtt_task import mqtt_task
from services.idle_task import idle_task
from services.led_task import led_task
#from services.fake_ap_activation_task import fake_ap_activation_task
from services.ap_auto_disable_task import ap_auto_disable_task
from services.serial_task import serial_task

from logger import Logger
log = Logger("main", debug_enabled=True)

# ---- Global variables ----
import shared_variables as var



async def main():
    
    # kick watchdog if you want (optional)
    #wdt = machine.WDT(timeout=8000)

    # spawn threads
    asyncio.create_task(idle_task(10))
    asyncio.create_task(led_task(0.1))
    asyncio.create_task(mqtt_task(10))
    asyncio.create_task(networking_task(10, 50))
    #asyncio.create_task(fake_ap_activation_task(20,500))
    asyncio.create_task(ap_auto_disable_task(1))
    asyncio.create_task(serial_task(0.05))

    while True:
    #    #wdt.feed()
        await asyncio.sleep(1)

def start():
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # important on MicroPython

# Auto-start when executed as script
start()
