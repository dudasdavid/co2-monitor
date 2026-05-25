import uasyncio as asyncio
import persistent_config

debug = False

class SimpleQueue:
    def __init__(self):
        self._items = []
        self._lock = asyncio.Lock()
        self._event = asyncio.Event()

    async def put(self, item):
        async with self._lock:
            self._items.append(item)
            self._event.set()

    def put_nowait(self, item):
        # Safe if everything runs on the same thread/core
        self._items.append(item)
        self._event.set()

    async def get(self):
        while True:
            await self._event.wait()

            async with self._lock:
                if self._items:
                    item = self._items.pop(0)

                    if not self._items:
                        self._event.clear()

                    return item
                else:
                    self._event.clear()

button_events = SimpleQueue()
haptic_events = SimpleQueue()

class SensorData:
    def __init__(self):
        self.temp_aht21 = 10.1
        self.temp_scd41 = 10.2
        self.temp_bmp280 = 10.3
        self.humidity_aht21 = 69.1
        self.humidity_scd41 = 96.1
        self.co2_scd41 = 666
        self.co2_rating_scd41 = "unknown"
        self.eco2_ens160 = 999
        self.eco2_rating_ens160 = "unknown"
        self.tvoc_ens160 = 100
        self.tvoc_rating_ens160 = "unknown"
        self.aqi_ens160  = 1
        self.aqi_rating_ens160 = "unknown"
        self.pressure_bmp280 = 1001
        self.lux_veml7700 = 222
        self.pm10_sps30 = None
        self.pm10_filtered_sps30 = None
        self.pm10_rating_sps30 = "unknown"
        self.pm4_sps30 = None
        self.pm4_filtered_sps30 = None
        self.pm4_rating_sps30 = "unknown"
        self.pm2_5_sps30 = None
        self.pm2_5_filtered_sps30 = None
        self.pm2_5_rating_sps30 = "unknown"
        self.pm1_sps30 = None
        self.pm1_filtered_sps30 = None
        self.pm1_rating_sps30 = "unknown"


class SystemData:
    def __init__(self):
        self.time_ntp = "ESP32C3 is OFFLINE"
        self.time_rtc = "2025-11-20 20:00:10"
        self.time_local = "NA"
        self.status_wifi = "ESP32C3 is OFFLINE"
        self.status_ap = "ESP32C3 is OFFLINE"
        self.status_mqtt = "ESP32C3 is OFFLINE"
        self.status_sd = "Offline"
        self.total_space_flash = 690
        self.used_space_flash = 69
        self.total_space_sd = 6900
        self.used_space_sd = 69
        self.total_heap = 6900
        self.used_heap = 69
        self.bl_duty_percent = 34
        self.i2c_devices = []
        self.i2c_status_scd41  = "NA"
        self.i2c_status_aht21  = "NA"
        self.i2c_status_ens160  = "NA"
        self.i2c_status_bmp280  = "NA"
        self.i2c_status_veml7700  = "NA"
        self.i2c_status_ds3231  = "NA"
        self.i2c_status_pca9685  = "NA"
        self.i2c_status_drv2605  = "NA"
        self.i2c_status_sps30  = "NA"
        self.i2c_status_unknown = [0x666]
        self.usb_volt = 4.85
        self.bat_volt = 3.8
        self.dcdc_volt = 4.69
        self.ideal_diode_volt = 5.0
        self.bat_percentage = 69
        self.charging = False
        self.feedback_led = [0,0,1000]
        self.adc_task_timestamp = 0
        self.backlight_task_timestamp = 0
        self.history_task_timestamp = 0
        self.i2c_task_timestamp = 0
        self.idle_task_timestamp = 0
        self.serial_task_timestamp = 0
        self.storage_task_timestamp = 0
        self.io_task_timestamp = 0
        self.led_task_timestamp = 0
        self.button = 2


# SPS30 filter strength (lower = smoother but slower)
sps30_alpha_slow = 0.03
sps30_alpha_fast = 0.15

aht21_temp_offset = 0

# Max number of samples you expect (24h at 5 min)
CO2_HISTORY_MAX = 12 * 24

scd41_co2_peak_ppm = 400
scd41_co2_threshold = 1800
scd41_co2_detected = 0
scd41_co2_history = [400] # Must contain 1 placeholder element

history_loaded = False

try:
    TZ_OFFSET = persistent_config.TZ_OFFSET
except:
    print("TZ offset cannot be read from persistent_config.py!")
    TZ_OFFSET = 0

sensor_data = SensorData()
system_data = SystemData()

# screens are main screens, alt screens are a second page of screens
screens = []
screens_alt = []
screen_names = []
screen_names_alt = []
current_idx = 0
current_idx_alt = 0
# flag to show if alternative or game screen is selected
selected_alt = 0

touch_start_x = 0
touch_start_y = 0
last_y = 0

logger_paused = False
logger_error = []
logger_label_prev = ""

ap_request = False
wifi_connected = False

EVENT_FB_SWIPE_LEFT = 1
EVENT_FB_SWIPE_RIGHT = 2
EVENT_FB_LONG_PRESS = 3
EVENT_BUTTON_PRESS = 1
EVENT_BUTTON_LONG_PRESS = 2