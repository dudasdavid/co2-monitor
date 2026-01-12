import uasyncio as asyncio
from umqtt.simple import MQTTClient
import umqtt.config
import time

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
    client = MQTTClient(client_id=MQTT_CLIENT_ID,
                        server=MQTT_SERVER,
                        port=MQTT_PORT,
                        user=MQTT_USER,
                        password=MQTT_PASSWORD,
                        keepalive=MQTT_KEEPALIVE,
                        ssl=MQTT_SSL,
                        ssl_params=MQTT_SSL_PARAMS)

    #Run
    while True:
        
        await var.wifi_ready_evt.wait()
        log.info("Successful WiFi connection event received!")
        
        try:
            log.info("Connecting to MQTT server...")
            await asyncio.sleep(0.1)
            client.connect()
            await asyncio.sleep(5)
            log.info("Publishing data...")
            if var.co2_detected is not None:
                client.publish("co2_monitor/detected", str(var.co2_detected))
            if var.co2 is not None:
                client.publish("co2_monitor/level", str(var.co2))
            if var.co2_peak is not None:
                client.publish("co2_monitor/peak_level", str(var.co2_peak))
            if var.temperature is not None:
                client.publish("co2_monitor/temperature", str(var.temperature))
            if var.humidity is not None:
                client.publish("co2_monitor/humidity", str(var.humidity))
            if var.aqi is not None:
                client.publish("co2_monitor/aqi", str(var.aqi))
            if var.tvoc is not None:
                client.publish("co2_monitor/tvoc", str(var.tvoc))
            if var.lux is not None:
                client.publish("co2_monitor/lux", str(var.lux))
                
            await asyncio.sleep(0.1)
            log.info("Disconnecting from MQTT server...")
            client.disconnect()

        except Exception as e:
            log.error("Exception:", e)

        await asyncio.sleep(period)
        
if __name__ == "__main__":
    print("TESTING SINGLE TASK!")
    asyncio.run(mqtt_task(10))