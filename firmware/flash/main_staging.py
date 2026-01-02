import gc

import lvgl as lv
lv.init()
import lvstm32 as st
st.lvstm32()
import rk043fn48h as rk
rk.init()

import uasyncio as asyncio
import machine
from services.idle_task import idle_task
from services.serial_task import serial_task
from services.i2c_task import i2c_task
from services.backlight_task import backlight_task
from services.storage_task import storage_task
from services.history_task import history_task
from services.adc_task import adc_task

from logger import Logger

# UI will be loaded from SD card
import ui1
import ui2

# ---- Global variables ----
import shared_variables as var

def init_display():
    
    disp_buf1 = lv.disp_buf_t()
    buf1_1 = bytes(480 * 80)
    disp_buf1.init(buf1_1, None, len(buf1_1) // 4)
    disp_drv = lv.disp_drv_t()
    disp_drv.init()
    disp_drv.buffer = disp_buf1
    disp_drv.flush_cb = rk.flush
    disp_drv.hor_res = 480
    disp_drv.ver_res = 272
    disp_drv.register()

    indev_drv = lv.indev_drv_t()
    indev_drv.init()
    indev_drv.type = lv.INDEV_TYPE.POINTER
    indev_drv.read_cb = rk.ts_read
    indev_drv.register()


async def main():
    
    log = Logger("main", debug_enabled=False)
    
    # kick watchdog if you want (optional)
    #wdt = machine.WDT(timeout=8000)


    log.info("LVGL version:", lv.version_major(), lv.version_minor(), lv.version_patch())
    gc.collect()
    log.info("Free RAM before lv.obj():", gc.mem_free())
    
    #lv.init()
    #st.lvstm32()
    init_display()
    
    top_layer = lv.layer_top()
    

    # 1) spawn threads
    asyncio.create_task(idle_task(5.0))
    asyncio.create_task(serial_task(0.5))
    asyncio.create_task(i2c_task(0.3))
    asyncio.create_task(backlight_task(0.4))
    asyncio.create_task(storage_task(3))
    asyncio.create_task(history_task(2))
    asyncio.create_task(adc_task(0.5))

    # 3) main loop can do supervision / LEDs / watchdog
    led = machine.Pin("LED", machine.Pin.OUT)

    # Create some demo screens
    ui2.create_co2_chart()
    ui1.create_sensor_table()
    ui1.create_system_table()
    ui1.create_console_log()
    #ui2.create_screen(0x202040, "Screen 1")
    #ui2.create_screen(0x204020, "Screen 2")

    ui1.show_screen(0)   # start with screen 0

    ui2.create_status_bar(top_layer)


    log.info("Free RAM after lv.obj():", gc.mem_free())

    while True:
        #wdt.feed()
        await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()


