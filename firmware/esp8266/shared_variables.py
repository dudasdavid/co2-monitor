# shared_variables.py
import uasyncio as asyncio

HTTP_STATE = {
    "OccupancyDetected": False,
    "Active": False,
    "Fault": False,
    "LowBattery": False,
    "Tampered": False,
}

_http_lock = asyncio.Lock()

UTC_OFFSET = 1 * 3600

occupancy_detected = False
active = True
fault = False
low_battery = False
tampered = False
battery_level = 69

pir_detected = False
mm_wave_detected = False

lux = 0.001