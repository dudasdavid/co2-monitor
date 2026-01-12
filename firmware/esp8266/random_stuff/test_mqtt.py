import uasyncio as asyncio
from umqtt.simple import MQTTClient
import umqtt.config
import time
import network
import socket
import ntptime
from my_wifi import SSID, PASSWORD

from logger import Logger

# ---- Global variables ----
import shared_variables as var

log = Logger("mqtt", debug_enabled=True)

# MQTT Parameters
MQTT_SERVER = umqtt.config.mqtt_server
MQTT_PORT = 1883
MQTT_USER = umqtt.config.mqtt_username
MQTT_PASSWORD = umqtt.config.mqtt_password
MQTT_CLIENT_ID = b"esp8266"
MQTT_KEEPALIVE = 7200
MQTT_SSL = False   # set to False if using local Mosquitto MQTT broker
MQTT_SSL_PARAMS = {'server_hostname': MQTT_SERVER}

async def wifi_connect(wlan):

    # ---- CONNECT TO WIFI ----
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    log.info("Connecting to WiFi...")
    while not wlan.isconnected():
        print(".", end="")
        await asyncio.sleep_ms(500)

    log.info("Connected!")
    log.info("IP address:", wlan.ifconfig()[0])

    # ---- SYNC TIME FROM NTP ----
    log.info("Fetching time from NTP...")
    try:
        ntptime.settime()  # sets internal RTC to UTC
        log.info("Time synchronized.")
    except Exception as e:
        log.error("NTP sync failed:", e)

def wifi_disconnect(wlan):
    try:
        log.info("Disconnecting from WiFi...")
        wlan.disconnect()
    except Exception as e:
        log.error("WiFi disconnection failed:", e)
    wlan.active(False)

def _now_ms():
    # Prefer monotonic ticks on MicroPython
    try:
        return time.ticks_ms()
    except AttributeError:
        # Fallback (lower resolution, not wrap-safe)
        return int(time.time() * 1000)

def _ms_since(t0_ms, t1_ms):
    # Wrap-safe if ticks_ms exists
    try:
        return time.ticks_diff(t1_ms, t0_ms)
    except AttributeError:
        return t1_ms - t0_ms
    
async def mqtt_task(period = 1.0):
    #Init
    wlan = network.WLAN(network.STA_IF)
    
    await wifi_connect(wlan)

    client = MQTTClient(client_id=MQTT_CLIENT_ID,
                        server=MQTT_SERVER,
                        port=MQTT_PORT,
                        user=MQTT_USER,
                        password=MQTT_PASSWORD,
                        keepalive=MQTT_KEEPALIVE,
                        ssl=MQTT_SSL,
                        ssl_params=MQTT_SSL_PARAMS)
    
    client.connect()

    #Run
    while True:
        
        client.publish("co2_monitor/detected", str(0))
        client.publish("co2_monitor/level", str(1111))
        client.publish("co2_monitor/peak_level", str(1222))

        await asyncio.sleep(period)
        
if __name__ == "__main__":
    print("TESTING SINGLE TASK!")
    asyncio.run(mqtt_task(10))
