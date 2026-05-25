
class SensorData:
    def __init__(self):
        self.temp_aht21 = 18.1
        self.temp_scd41 = 19.2
        self.temp_bmp280 = 18.5
        self.humidity_aht21 = 59.1
        self.humidity_scd41 = 69.2
        self.co2_scd41 = 420
        self.co2_rating_scd41 = "Excellent"
        self.eco2_ens160 = 430
        self.eco2_rating_ens160 = "Excellent"
        self.tvoc_ens160 = 200
        self.tvoc_rating_ens160 = "Good"
        self.aqi_ens160  = 3
        self.aqi_rating_ens160 = "Moderate"
        self.pressure_bmp280 = 1021
        self.lux_veml7700 = 252
        self.pm10_sps30 = 140
        self.pm10_rating_sps30 = "Poor"
        self.pm4_sps30 = 100
        self.pm4_rating_sps30 = "Unhealthy"
        self.pm2_5_sps30 = 25
        self.pm2_5_rating_sps30 = "Moderate"
        self.pm1_sps30 = 10
        self.pm1_rating_sps30 = "Good"


class SystemData:
    def __init__(self):
        self.time_ntp = (2025, 11, 20, 0, 9, 32, 10)
        self.time_rtc = (2025, 11, 20, 0, 9, 32, 10)
        self.time_local = (2025, 11, 20, 0, 11, 32, 10)
        self.status_wifi = "WiFi Connected | 192.168.1.69"
        self.status_ap = "Disabled"
        self.status_mqtt = "Remote"
        self.status_sd = "Online"
        self.total_space_flash = 690
        self.used_space_flash = 69
        self.total_space_sd = 6900
        self.used_space_sd = 69
        self.total_heap = 6900
        self.used_heap = 69
        self.bl_duty_percent = 650
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
        self.bat_percentage = 100
        self.charging = True
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
aht21_humidity_offset = 0

# Max number of samples you expect (24h at 5 min)
CO2_HISTORY_MAX = 12 * 24

scd41_co2_peak_ppm = 400
scd41_co2_threshold = 1800
scd41_co2_detected = 0
scd41_co2_history = [
    500, 595, 700, 795, 880, 920, 950, 950,
    922, 890, 838, 800, 760, 722, 688, 660,
    638, 622, 610, 603, 600, 606, 620, 642,
    672, 710, 757, 813, 878, 952, 1035, 1127,
    1228, 1338, 1457, 1585, 1720, 1760, 1800, 1798,
    1795, 1791, 1786, 1780, 1773, 1765, 1756, 1746
]

scd41_co2_max_history_samples = 60

history_loaded = False


free_space = 0
all_space = 0
 
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

btn_left = None
btn_right = None

logger_paused = False
logger_error = ["#ff0000 ERROR#: Sensor read failed!",
                "#ffff00 WARN#: WiFi connection unstable!",
                "#00ff00 INFO#: System running smoothly!",
                "#00ffff DEBUG#: Debugging info here..."]
logger_label_prev = ""

ap_request = False
wifi_connected = True
