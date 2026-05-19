import uasyncio as asyncio
from logger import Logger
import time
from ui import ui_generic

# ---- Global variables ----
import shared_variables as var

async def event_handler_task():
    #Init
    log = Logger("evnt", debug_enabled=True)

    #Run
    while True:
        # wait for next event (this blocks until something arrives)
        event_type = await var.button_events.get()

        if event_type == var.EVENT_BUTTON_PRESS:
            log.debug("SHORT press detected")
            ui_generic.next_screen()
            #await var.audio_events.put(var.EVENT_AUDIO_SHORT)

        elif event_type == var.EVENT_BUTTON_LONG_PRESS:
            log.debug("LONG press detected")
            await var.haptic_events.put(var.EVENT_FB_LONG_PRESS)

        else:
            log.debug("Unknown event:", btn_name, event_type)
