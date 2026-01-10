import uasyncio as asyncio
from umqtt.simple import MQTTClient
import umqtt.config
import time

from logger import Logger

# ---- Global variables ----
import shared_variables as var

# Constants for MQTT Topics
MQTT_TOPIC = 'test'

# MQTT Parameters
MQTT_SERVER = umqtt.config.mqtt_server
MQTT_PORT = 1883
MQTT_USER = umqtt.config.mqtt_username
MQTT_PASSWORD = umqtt.config.mqtt_password
MQTT_CLIENT_ID = b"raspberrypi_pico2w"
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
    log = Logger("mqtt", debug_enabled=False)

    try:
        client = MQTTClient(client_id=MQTT_CLIENT_ID,
                            server=MQTT_SERVER,
                            port=MQTT_PORT,
                            user=MQTT_USER,
                            password=MQTT_PASSWORD,
                            keepalive=MQTT_KEEPALIVE,
                            ssl=MQTT_SSL,
                            ssl_params=MQTT_SSL_PARAMS)
        client.connect()

    except Exception as e:
        log.error('Error connecting to MQTT:', e)
        raise  # Re-raise the exception to see the full traceback

    occupancy_detected_prev = None
    active_prev = None
    fault_prev = None
    low_battery_prev = None
    tampered_prev = None
    lux_prev = 0
    battery_level_prev = 42
    
    last_send_occupancy_ms = 0
    last_send_active_ms = 0
    last_send_fault_ms = 0
    last_send_low_battery_ms = 0
    last_send_battery_level_ms = 0
    last_send_tampered_ms = 0
    last_send_lux_ms = 0
    resend_grace_ms = int(30 * 1000)
    minimum_resend_time_ms = int(10*1000)

    #Run
    while True:
        
        now = _now_ms()
        
        occupancy_detected_temp = var.occupancy_detected
        if occupancy_detected_temp != occupancy_detected_prev or _ms_since(last_send_occupancy_ms, now) > resend_grace_ms:
            occupancy_detected_prev = occupancy_detected_temp
            client.publish("pico_motion/occupancy_detected", str(int(occupancy_detected_temp)))
            last_send_occupancy_ms = now
            log.debug("Occupancy updated:", occupancy_detected_temp)
        
        active_temp = var.active
        if active_temp != active_prev or _ms_since(last_send_active_ms, now) > resend_grace_ms:
            active_prev = active_temp
            client.publish("pico_motion/active", str(int(active_temp)))
            last_send_active_ms = now
        
        fault_temp = var.fault
        if fault_temp != fault_prev or _ms_since(last_send_fault_ms, now) > resend_grace_ms:
            fault_prev = fault_temp
            client.publish("pico_motion/fault", str(int(fault_temp)))
            last_send_fault_ms = now

        low_battery_temp = var.low_battery
        if low_battery_temp != low_battery_prev or _ms_since(last_send_low_battery_ms, now) > resend_grace_ms:
            low_battery_prev = low_battery_temp
            client.publish("pico_motion/low_battery", str(int(low_battery_temp)))
            last_send_low_battery_ms = now

        battery_level_temp = var.battery_level
        if battery_level_temp != battery_level_prev or _ms_since(last_send_battery_level_ms, now) > resend_grace_ms:
            battery_level_prev = battery_level_temp
            client.publish("pico_motion/battery_level", str(int(battery_level_temp)))
            last_send_battery_level_ms = now

        tampered_temp = var.tampered
        if tampered_temp != tampered_prev or _ms_since(last_send_tampered_ms, now) > resend_grace_ms:
            tampered_prev = tampered_temp
            client.publish("pico_motion/tampered", str(int(tampered_temp)))
            last_send_tampered_ms = now
            
        lux_temp = var.lux
        if (lux_temp != lux_prev or _ms_since(last_send_lux_ms, now) > resend_grace_ms) and _ms_since(last_send_lux_ms, now) > minimum_resend_time_ms:
            lux_prev = lux_temp
            if lux_temp < 0.001:
                lux_temp = 0.001
            
            client.publish("pico_motion/lux", str(lux_temp))
            last_send_lux_ms = now

        await asyncio.sleep(period)
