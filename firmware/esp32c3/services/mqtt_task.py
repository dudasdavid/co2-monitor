from umqtt.simple import MQTTClient
import uasyncio as asyncio
import umqtt.config
import time
import json

from logger import Logger

# ---- Global variables ----
import shared_variables as var

log = Logger("mqtt", debug_enabled=True)

# MQTT Parameters for LAN connection
MQTT_SERVER_LOCAL = umqtt.config.mqtt_server_local
MQTT_PORT_LOCAL = umqtt.config.mqtt_port_local
MQTT_USER_LOCAL = umqtt.config.mqtt_username_local
MQTT_PASSWORD_LOCAL = umqtt.config.mqtt_password_local
MQTT_SSL_LOCAL = False   # set to False if using local Mosquitto MQTT broker
MQTT_SSL_PARAMS_LOCAL = {'server_hostname': MQTT_SERVER_LOCAL}

# MQTT Parameters for remote internet connection
MQTT_SERVER_REMOTE = umqtt.config.mqtt_server_remote
MQTT_PORT_REMOTE = umqtt.config.mqtt_port_remote
MQTT_USER_REMOTE = umqtt.config.mqtt_username_remote
MQTT_PASSWORD_REMOTE = umqtt.config.mqtt_password_remote
MQTT_SSL_REMOTE = False   # set to False if using local Mosquitto MQTT broker
MQTT_SSL_PARAMS_REMOTE = {'server_hostname': MQTT_SERVER_REMOTE}

# MQTT generic parameters
MQTT_CLIENT_ID = var.hostname.encode()
MQTT_KEEPALIVE = 7200

MQTT_ENDPOINTS = [
    {
        "name": "Local",
        "server": MQTT_SERVER_LOCAL,
        "port": MQTT_PORT_LOCAL,
        "user": MQTT_USER_LOCAL,
        "password": MQTT_PASSWORD_LOCAL,
        "ssl": MQTT_SSL_LOCAL,
        "ssl_params": MQTT_SSL_PARAMS_LOCAL,
    },
    {
        "name": "Remote",
        "server": MQTT_SERVER_REMOTE,
        "port": MQTT_PORT_REMOTE,
        "user": MQTT_USER_REMOTE,
        "password": MQTT_PASSWORD_REMOTE,
        "ssl": MQTT_SSL_REMOTE,
        "ssl_params": MQTT_SSL_PARAMS_REMOTE,
    },
]

last_mqtt_endpoint = 0   # 0 = local first, 1 = remote first

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

def make_client(ep):
    return MQTTClient(
        client_id=MQTT_CLIENT_ID,
        server=ep["server"],
        port=ep["port"],
        user=ep["user"],
        password=ep["password"],
        keepalive=MQTT_KEEPALIVE,
        ssl=ep["ssl"],
        ssl_params=ep["ssl_params"],
    )

def connect_mqtt():
    global last_mqtt_endpoint

    order = [
        last_mqtt_endpoint,
        1 - last_mqtt_endpoint,
    ]

    last_error = None

    for idx in order:
        ep = MQTT_ENDPOINTS[idx]
        client = make_client(ep)
        try:
            log.info("Trying MQTT", ep["name"], ep["server"], ep["port"])
            client.connect()
            
            last_mqtt_endpoint = idx
            log.info("MQTT connected via", ep["name"])
            return client, ep["name"]

        except Exception as e:
            last_error = e
            log.warning("MQTT", ep["name"], "failed:", e)

            try:
                client.disconnect()
            except Exception:
                pass

    raise OSError("Both MQTT endpoints failed: " + str(last_error))

async def mqtt_task(period = 1.0):
    #Init
    client = None

    DISCOVERY_PREFIX = "homeassistant"
    BASE_TOPIC = "custom_sensors/co2_big_screen"

    DEVICE_ID = "co2_big_screen"
    DEVICE_NAME = "CO2 Big Screen"
    
    device = {
        "identifiers": [DEVICE_ID],
        "name": DEVICE_NAME,
        "manufacturer": "Custom",
        "model": "Custom Sensor",
    }

    def _pub(client, topic: str, payload: dict, retain: bool = True):
        client.publish(topic.encode(), json.dumps(payload).encode(), retain=retain)

    # ----- Helpers to create entity payloads -----
    def sensor(unique_id, name, state_topic, unit=None, device_class=None, icon=None):
        p = {
            "name": name,
            "state_topic": state_topic,
            "unique_id": unique_id,
            "device": device,
        }
        if unit is not None:
            p["unit_of_measurement"] = unit
        if device_class is not None:
            p["device_class"] = device_class
        if icon is not None:
            p["icon"] = icon
        return p

    def binary_sensor(unique_id, name, state_topic, device_class=None,
                      payload_on="1", payload_off="0", icon=None):
        p = {
            "name": name,
            "state_topic": state_topic,
            "unique_id": unique_id,
            "device": device,
            "payload_on": payload_on,
            "payload_off": payload_off,
        }
        if device_class is not None:
            p["device_class"] = device_class
        if icon is not None:
            p["icon"] = icon
        return p

    def publish_discovery(client):
        """
        Publish HA MQTT discovery config for all sensors.
        Call once at boot (or after MQTT reconnect). Uses retain=True.
        """

        # ----- Publish discovery configs (retain=True) -----

        # CO2 level (ppm)
        _pub(client,
             f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}_co2/config",
             sensor(f"{DEVICE_ID}_co2", "CO2 Level", f"{BASE_TOPIC}/co2_level",
                    unit="ppm", device_class="carbon_dioxide"))

        # CO2 peak (ppm)
        _pub(client,
             f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}_co2_peak/config",
             sensor(f"{DEVICE_ID}_co2_peak", "CO2 Peak Level", f"{BASE_TOPIC}/co2_peak_level",
                    unit="ppm", device_class="carbon_dioxide"))

        # Temperature (°C)
        _pub(client,
             f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}_temperature/config",
             sensor(f"{DEVICE_ID}_temperature", "Temperature", f"{BASE_TOPIC}/temperature",
                    unit="°C", device_class="temperature"))

        # Humidity (%)
        _pub(client,
             f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}_humidity/config",
             sensor(f"{DEVICE_ID}_humidity", "Humidity", f"{BASE_TOPIC}/humidity",
                    unit="%", device_class="humidity"))

        # AQI (unitless index) – HA doesn't have a universal device_class for AQI everywhere,
        # so we leave device_class unset and just name it clearly.
        _pub(client,
             f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}_aqi/config",
             sensor(f"{DEVICE_ID}_aqi", "AQI", f"{BASE_TOPIC}/aqi",
                    icon="mdi:air-filter"))

        # TVOC (ppb) – many people use ppb; if yours is different, change unit here.
        _pub(client,
             f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}_tvoc/config",
             sensor(f"{DEVICE_ID}_tvoc", "TVOC", f"{BASE_TOPIC}/tvoc",
                    unit="ppb", icon="mdi:chemical-weapon"))

        # Lux (lx)
        _pub(client,
             f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}_lux/config",
             sensor(f"{DEVICE_ID}_lux", "Illuminance", f"{BASE_TOPIC}/lux",
                    unit="lx", device_class="illuminance"))

        # Battery (%)
        _pub(client,
             f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}_battery/config",
             sensor(f"{DEVICE_ID}_battery", "Battery", f"{BASE_TOPIC}/battery",
                    unit="%", device_class="battery"))

        # Low battery (binary)
        _pub(client,
             f"{DISCOVERY_PREFIX}/binary_sensor/{DEVICE_ID}_low_battery/config",
             binary_sensor(f"{DEVICE_ID}_low_battery", "Low Battery", f"{BASE_TOPIC}/low_battery",
                           device_class="battery", payload_on="1", payload_off="0"))

        # Air pressure (hPa) – if you publish Pa, switch unit to "Pa" and/or scale your value.
        _pub(client,
             f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}_air_pressure/config",
             sensor(f"{DEVICE_ID}_air_pressure", "Air Pressure", f"{BASE_TOPIC}/air_pressure",
                    unit="hPa", device_class="atmospheric_pressure"))

        # CO2 detected (binary)
        # If you publish True/False instead of 1/0, change payload_on/off accordingly.
        _pub(client,
             f"{DISCOVERY_PREFIX}/binary_sensor/{DEVICE_ID}_co2_detected/config",
             binary_sensor(f"{DEVICE_ID}_co2_detected", "CO2 Detected", f"{BASE_TOPIC}/co2_detected",
                           icon="mdi:molecule-co2", payload_on="1", payload_off="0"))

        # PM1.0 (µg/m³) - no official device_class
        _pub(client,
             f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}_pm1_0/config",
             sensor(f"{DEVICE_ID}_pm1_0", "PM1.0", f"{BASE_TOPIC}/pm1_0",
                    unit="µg/m³"))

        # PM2.5 (µg/m³)
        _pub(client,
             f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}_pm2_5/config",
             sensor(f"{DEVICE_ID}_pm2_5", "PM2.5", f"{BASE_TOPIC}/pm2_5",
                    unit="µg/m³", device_class="pm25"))

        # PM4.0 (µg/m³) - no official device_class
        _pub(client,
             f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}_pm4_0/config",
             sensor(f"{DEVICE_ID}_pm4_0", "PM4.0", f"{BASE_TOPIC}/pm4_0",
                    unit="µg/m³"))

        # PM10 (µg/m³)
        _pub(client,
             f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}_pm10/config",
             sensor(f"{DEVICE_ID}_pm10", "PM10", f"{BASE_TOPIC}/pm10",
                    unit="µg/m³", device_class="pm10"))

    #Run
    while True:
        
        await var.wifi_ready_evt.wait()
        log.info("Successful WiFi connection event received!")
        
        client = None
        
        try:
            log.debug("Connecting to MQTT server...")
            await asyncio.sleep(0.1)
            client, mqtt_name = connect_mqtt()
            var.mqqt_server_connection = mqtt_name
            await asyncio.sleep(5)
            
            # Publish HA discovery with retain once after startup
            if var.first_connect:
                var.first_connect = False
                publish_discovery(client)
            
            if var.co2_detected is not None:
                client.publish("custom_sensors/co2_big_screen/co2_detected", str(var.co2_detected))
            if var.co2 is not None:
                client.publish("custom_sensors/co2_big_screen/co2_level", str(int(var.co2)))
            if var.co2_peak is not None:
                client.publish("custom_sensors/co2_big_screen/co2_peak_level", str(int(var.co2_peak)))
            if var.temperature is not None:
                client.publish("custom_sensors/co2_big_screen/temperature", f"{var.temperature:.1f}")
            if var.humidity is not None:
                client.publish("custom_sensors/co2_big_screen/humidity", f"{var.humidity:.1f}")
            if var.aqi is not None:
                client.publish("custom_sensors/co2_big_screen/aqi", str(int(var.aqi)))
            if var.tvoc is not None:
                client.publish("custom_sensors/co2_big_screen/tvoc", str(int(var.tvoc)))
            if var.lux is not None:
                client.publish("custom_sensors/co2_big_screen/lux", f"{var.lux:.4f}")
            if var.battery is not None:
                client.publish("custom_sensors/co2_big_screen/battery", str(int(var.battery)))
                low_battery = 0
                if var.battery < 20:
                    low_battery = 1
                client.publish("custom_sensors/co2_big_screen/low_battery", str(low_battery))
            if var.pressure is not None:
                client.publish("custom_sensors/co2_big_screen/air_pressure", str(var.pressure))
            if var.pm10 is not None:
                client.publish("custom_sensors/co2_big_screen/pm10", str(var.pm10))
            if var.pm4_0 is not None:
                client.publish("custom_sensors/co2_big_screen/pm4_0", str(var.pm4_0))
            if var.pm2_5 is not None:
                client.publish("custom_sensors/co2_big_screen/pm2_5", str(var.pm2_5))
            if var.pm1_0 is not None:
                client.publish("custom_sensors/co2_big_screen/pm1_0", str(var.pm1_0))
                
            log.info("Successfuly published data to MQTT server")
                
            await asyncio.sleep(0.1)

        except Exception as e:
            log.error("MQTT publish failed:", e)
            var.mqqt_server_connection = "Server error"
            
        finally:
            if client:
                try:
                    log.debug("Disconnecting from MQTT server...")
                    client.disconnect()
                except Exception:
                    log.error("Disconnecting from MQTT server failed!")
                    pass

        await asyncio.sleep(period)
        
if __name__ == "__main__":
    print("TESTING SINGLE TASK!")
    asyncio.run(mqtt_task(10))