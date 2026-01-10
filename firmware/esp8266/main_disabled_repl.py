import uasyncio as asyncio
from machine import Pin
from services.idle_task import idle_task
import time

import network
import socket
import ntptime
from my_wifi import SSID, PASSWORD

from logger import Logger
log = Logger("main", debug_enabled=True)

# ---- Global variables ----
import shared_variables as var

def wifi_connect():

    # ---- CONNECT TO WIFI ----
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    log.info("Connecting to WiFi...")
    while not wlan.isconnected():
        print(".", end="")
        time.sleep(0.5)

    log.info("Connected!")
    log.info("IP address:", wlan.ifconfig()[0])

    # ---- SYNC TIME FROM NTP ----
    log.info("Fetching time from NTP...")
    try:
        ntptime.settime()  # sets internal RTC to UTC
        log.info("Time synchronized.")
    except Exception as e:
        log.error("NTP sync failed:", e)

async def main():
    
    # kick watchdog if you want (optional)
    #wdt = machine.WDT(timeout=8000)
    led = Pin(2, Pin.OUT)

    # 1) bring up network in main thread (safer)
    wifi_connect()

    # 2) spawn threads
    asyncio.create_task(idle_task(10))

    while True:
    #    #wdt.feed()
        led.toggle()
        await asyncio.sleep(1)

def start():
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # important on MicroPython

# Auto-start when executed as script
start()
