import uasyncio as asyncio
from machine import I2C
from drivers import ssd1306
from logger import Logger
import time

# ---- Global variables ----
import shared_variables as var
 
async def display_task(period = 1.0):
    #Init
    log = Logger("display", debug_enabled=True)
    
    i2c=I2C(0, freq=100000, scl=6, sda=5)
    log.info("I2C scan:", i2c.scan())
    
    display = ssd1306.SSD1306_I2C(72, 40, i2c)

    msg = ""
    x = display.width   # start just off the right edge

    #Run
    while True:

        display.fill(0)
        
        if var.wifi_connected:
            msg = var.wifi_ip
            header = "Connected"
        elif var.ap_enabled:
            msg = "192.168.4.1"
            header = "AP active"
        elif var.wifi_sleep:
            msg = str(int(var.sleep_till_next_connection)) + " s"
            header = "Sleep"
        else:
            msg = "No idea"
            header = "No idea"
        
        # 8px per character in this font
        msg_w = len(msg) * 8
        
        display.text(header, 0, 0, 1)
        display.text(msg, x, 20, 1)
        display.show()

        if len(msg) > 8:
            x -= 2  # scroll speed (try 1..4)
            if x < -msg_w:
                x = display.width
        else:
            x = 0
            
        await asyncio.sleep(period)
