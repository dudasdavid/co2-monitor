class SensorData:
    def __init__(self):
        self.temp_aht21 = 10.1
        self.temp_scd41 = 10.2
        self.temp_bmp280 = 10.3
        self.temp_ens160 = 10.4
        self.humidity_aht21 = 69.1
        self.humidity_scd41 = 96.1
        self.humidity_ens160 = 97.1
        self.co2_scd41 = 666
        self.eco2_ens160 = 999
        self.eco2_rating_ens160 = "excellent"
        self.tvoc_ens160 = 100
        self.tvoc_rating_ens160 = "excellent"
        self.aqi_ens160  = 1
        self.pressure_bmp280 = 1001
        self.lux_veml7700 = 222


class SystemData:
    def __init__(self):
        self.time_ntp = "Not connected"
        self.time_rtc = "2025-11-20 20:00:10"
        self.status_wifi = "Not Connected"
        self.status_sd = "Offline"
        self.total_space_flash = 690
        self.used_space_flash = 69
        self.total_space_sd = 6900
        self.used_space_sd = 69
        self.total_heap = 6900
        self.used_heap = 69
        self.bl_duty_percent = 34
        self.i2c_status_scd41  = "online"
        self.i2c_status_aht21  = "online"
        self.i2c_status_ens160  = "online"
        self.i2c_status_bmp280  = "online"
        self.i2c_status_veml7700  = "online"
        self.i2c_status_ds3231  = "online"
        self.i2c_status_unknown = [0x69]
        self.usb_volt = 4.85
        self.bat_volt = 3.8
        self.dcdc_volt = 4.69
        self.bat_percentage = 69
        self.charging = False
        self.feedback_led = "green"


aht21_temp_offset = 0
aht21_humidity_offset = 0

# Max number of samples you expect (24h at 5 min)
CO2_HISTORY_MAX = 12 * 24

scd41_co2_peak_ppm = 400
scd41_co2_threshold = 1300
scd41_co2_detected = 0
scd41_co2_history = [400] # Must contain 1 placeholder element
scd41_co2_max_history_samples = 60

history_loaded = False

time_offset_ntp = 1

free_space = 0
all_space = 0
 
sensor_data = SensorData()
system_data = SystemData()

screens = []
screen_names = []
current_idx = 0

touch_start_x = 0
touch_start_y = 0
last_y = 0

btn_left = None
btn_right = None

logger_paused = False
logger_debug = ["empty"]
logger_info = ["empty"]
logger_error = ["empty"]
logger_warning = ["empty"]

logger_label_prev = ""
logger_current_view = logger_debug


