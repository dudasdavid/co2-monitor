import uasyncio as asyncio
from logger import Logger
import time

# ---- Global variables ----
import shared_variables as var

async def backlight_task(period = 1.0):
    #Init
    log = Logger("bclt", debug_enabled=False)
    
    lux_min=5.0       # below this treat as "dark"
    lux_max=500.0     # above this -> max backlight
    duty_min=50       # min duty on your 0..1000 scale (to avoid pitch black)
    duty_max=1000     # max duty
    gamma=2.0         # >1.0 compresses the low end (fixes "too bright at 10–15%")
    alpha=0.3          # smoothing factor (0..1), 0=no change, 1=no smoothing
    _level = 0.0       # internal smoothed brightness level [0..1]
    _duty = 0.0

    def _lux_to_level(lux):
        """Map lux → linear brightness level [0..1] (before gamma)."""
        if lux <= lux_min:
            return 0.0
        if lux >= lux_max:
            return 1.0

        # Normalize
        return (lux - lux_min) / (lux_max - lux_min)

    def _level_to_duty(level):
        """Map brightness level [0..1] → integer duty [duty_min..duty_max]."""
        # Clamp
        if level < 0.0:
            level = 0.0
        elif level > 1.0:
            level = 1.0

        # Apply gamma so small levels don't jump to "too bright"
        # hardware_effective = level ** gamma
        level_gamma = level ** gamma

        duty_range = duty_max - duty_min
        duty = duty_min + duty_range * level_gamma
        duty = int(duty + 0.5)
        
        if duty < 0:
            duty = 0
        elif duty > 1000:
            duty = 1000
            
        return duty
        

    #Run
    while True:
        log.debug("Measured lux:", var.sensor_data.lux_veml7700)
        
        raw_level = _lux_to_level(var.sensor_data.lux_veml7700)
        # Exponential smoothing to avoid flicker (optional)
        _level = (1.0 - alpha) * _level + alpha * raw_level
        _duty = _level_to_duty(_level)
            
        log.debug("Calculated duty [0-1000]:", _duty)
        var.system_data.bl_duty_percent = int(_duty)
        
        var.system_data.backlight_task_timestamp = time.time()
        
        await asyncio.sleep(period)
