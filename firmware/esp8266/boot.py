# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import os
import gc
import webrepl
webrepl.start()
gc.collect()

from machine import Pin
import time

# --- Pin definitions ---
PIN_OUT_TEST = 4   # GPIO4
PIN_IN_SENSE = 5   # GPIO5
PIN_OUT_RESULT = 2 # GPIO2 (TX1 pin on ESP8266, OK as output)

# --- Configure pins ---
test_out = Pin(PIN_OUT_TEST, Pin.OUT)
sense_in = Pin(PIN_IN_SENSE, Pin.IN)
result_out = Pin(PIN_OUT_RESULT, Pin.OUT)

# Default result OFF (which is inverted on ESP8266 module)
result_out.on()

# Small settle delay after boot
time.sleep_ms(50)

# --- Step 1: drive HIGH ---
test_out.on()
time.sleep_ms(10)
sense_high = sense_in.value()

# --- Step 2: drive LOW ---
test_out.off()
time.sleep_ms(10)
sense_low = sense_in.value()

# --- Evaluate ---
if sense_high == 1 and sense_low == 0:
    result_out.off() # Turn on-board LED ON (which is inverted on ESP8266 module)
    print("Pattern was detected, REPL gets disabled")
    
    # Detach REPL from UART0 (stream #1)
    os.dupterm(None, 1)
    
    import main_disabled_repl
    main_disabled_repl.start()
else:
    result_out.on() # Keep on-board LED OFF (which is inverted on ESP8266 module)
    print("Pattern was not detected, REPL stays enabled, main.py is not started")