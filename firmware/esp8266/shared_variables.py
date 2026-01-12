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

ap_request = False
ap_enabled = False
wifi_connected = False
wifi_connecting = False
ntp_time_synchronized = False
wifi_ready_evt = asyncio.Event()
ssid_save_successful = False
wifi_ip = None

occupancy_detected = False
active = True
fault = False
low_battery = False
tampered = False
battery_level = 69

pir_detected = False
mm_wave_detected = False

temperature = None
humidity = None
aqi = None
pm2_5 = None
pm10 = None
tvoc = None
co2 = None
co2_peak = None
co2_detected = None
lux = None