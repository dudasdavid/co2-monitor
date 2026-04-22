import uasyncio as asyncio
from machine import Pin
from logger import Logger
import time

# ---- Global variables ----
import shared_variables as var

log = Logger("io", debug_enabled=False)   

DEBOUNCE_MS = const(40)
LONG_PRESS_MS = const(800)

BTN         = "SW"

class ButtonHandler:
    def __init__(self, pin_num):
        self.pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)

        self.changed = False
        self.last_irq_ms = 0

        # Pin logic with PULL_UP:
        # 1 = released
        # 0 = pressed
        self.stable_state = self.pin.value()

        self.press_start_ms = None
        self.long_sent = False

        # Initialize global button state immediately
        var.system_data.button = int(not self.stable_state)

        self.pin.irq(
            trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
            handler=self._irq_handler
        )

    def _irq_handler(self, pin):
        now = time.ticks_ms()

        # tiny debounce at IRQ side
        if time.ticks_diff(now, self.last_irq_ms) < 5:
            return

        self.last_irq_ms = now
        self.changed = True
        
    async def run(self):
        while True:
            if self.changed:
                self.changed = False

                # proper debounce in async context
                await asyncio.sleep_ms(DEBOUNCE_MS)

                current_state = self.pin.value()

                # bounced back -> ignore
                if current_state == self.stable_state:
                    await asyncio.sleep_ms(5)
                    continue

                self.stable_state = current_state
                now = time.ticks_ms()

                # update shared button array immediately
                # pressed -> 1, released -> 0
                var.system_data.button = int(not current_state)

                if current_state == 1:
                    # pressed
                    self.press_start_ms = now
                    self.long_sent = False
                    asyncio.create_task(self._long_press_watch(self.press_start_ms))
                    log.debug("Pressed")

                else:
                    # released
                    if self.press_start_ms is not None:
                        press_time = time.ticks_diff(now, self.press_start_ms)

                        if (not self.long_sent) and press_time < LONG_PRESS_MS:
                            await var.button_events.put(var.EVENT_BUTTON_PRESS)
                            log.debug("SHORT press")

                    self.press_start_ms = None
                    self.long_sent = False
                    log.debug("Released")

            await asyncio.sleep_ms(5)

    async def _long_press_watch(self, start_ms):
        await asyncio.sleep_ms(LONG_PRESS_MS)

        if (
            self.press_start_ms == start_ms and
            self.stable_state == 1 and
            not self.long_sent
        ):
            self.long_sent = True
            await var.button_events.put(var.EVENT_BUTTON_LONG_PRESS)
            log.debug("LONG press")

async def io_task(period = 1.0):
    # Init button handlers
    btn = ButtonHandler(BTN)

    # Start button event tasks
    asyncio.create_task(btn.run())

    #Run
    while True:
        
        var.system_data.io_task_timestamp = time.time()
        
        await asyncio.sleep(period)
