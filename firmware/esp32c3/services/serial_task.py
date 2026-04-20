import uasyncio as asyncio
from machine import UART, Pin
from logger import Logger
import time

# ---- Global variables ----
import shared_variables as var

async def serial_task(period = 1.0):
    #Init
    log = Logger("uart", debug_enabled=True)
    
    uart = UART(0, baudrate=115200, bits=8, parity=None, stop=1, timeout=0)
    
    # ---- RX flush on init ----
    flushed = 0
    while uart.any():
        data = uart.read()
        if not data:
            break
        flushed += len(data)
        await asyncio.sleep(0)
    log.debug("RX flushed: {} bytes".format(flushed))
    
    request_timeout_ms = 3000
    max_buf_len = 100

    # ---- Simple request->response handler ----
    # You can replace this with your own protocol.
    def build_response(req: str) -> bytes:
        r = req.strip()  # strip whitespace + CR/LF
        
        log.debug(f"Received message: {r}")

        if not r:
            return b"ERR empty\r\n"

        # Example protocol:
        #   "PING" -> "PONG"
        if r == "PING":
            return b"PONG\r\n"
            
        if r == "WIFI_STATUS?":
            if var.wifi_connected:
                return "WiFi connected | {}\r\n".format(var.wifi_ip).encode()
            else:
                if var.wifi_connecting:
                    return b"WiFi connecting...\r\n"
                else:
                    return "Sleep {}s\r\n".format(int(var.sleep_till_next_connection)).encode()

        if r == "AP_STATUS?":
            if var.ap_enabled:
                return b"AP enabled | 192.168.4.1\r\n"
            else:
                if var.ap_request:
                    return b"AP requested\r\n"
                else:
                    return b"AP disabled\r\n"

        if r == "TIME?":
            if var.ntp_time_synchronized:
                return "TIME:{},{},{},{},{},{},{},{}\r\n".format(time.localtime()[0], time.localtime()[1], time.localtime()[2], time.localtime()[6], time.localtime()[3], time.localtime()[4], time.localtime()[5], time.localtime()[7]).encode()
            else:
                return b"NTP was not synchronized\r\n"
        
        if "TEMP:" in r:
            data_array = r[5:].split(",")
            var.temperature = float(data_array[0])
            var.humidity = float(data_array[1])
            return None

        if "AQI:" in r:
            data_array = r[4:].split(",")
            var.aqi = float(data_array[0])
            var.tvoc = float(data_array[1])
            return None

        if "CO2:" in r:
            data_array = r[4:].split(",")
            var.co2 = float(data_array[0])
            var.co2_peak = float(data_array[1])
            var.co2_detected = int(data_array[2])
            return None

        if "LUX:" in r:
            data_array = r[4:].split(",")
            var.lux = float(data_array[0])
            return None
        
        if "PRE:" in r:
            data_array = r[4:].split(",")
            var.pressure = float(data_array[0])
            return None
        
        if "BAT:" in r:
            data_array = r[4:].split(",")
            var.battery = float(data_array[0])
            return None
        
        if "PM:" in r:
            data_array = r[3:].split(",")
            var.pm10 = float(data_array[0])
            var.pm4_0 = float(data_array[1])
            var.pm2_5 = float(data_array[2])
            var.pm1_0 = float(data_array[3])
            return None

        # default: echo
        return "ECHO {}\r\n".format(r).encode()

    # ---- Main loop ----
    buf = bytearray()
    last_rx_ms = time.ticks_ms()

    while True:
        # wait for some data
        if not uart.any():
            await asyncio.sleep(period)
            continue

        # read available bytes (may contain 0..N frames)
        chunk = uart.read()
        if not chunk:
            await asyncio.sleep(period)
            continue

        buf.extend(chunk)
        last_rx_ms = time.ticks_ms()

        # safety: cap buffer (prevents RAM blowup if peer spams without CRLF)
        if len(buf) > max_buf_len:
            log.debug(f"RX buffer overflow (len={len(buf)}), clearing")
            #buf.clear()
            buf = bytearray()
            uart.write(b"ERR overflow\r\n")
            continue

        # extract and process ALL complete frames currently in buffer
        while True:
            i = buf.find(b"\n")
            if i < 0:
                break  # no complete frame yet, keep partial data in buf

            frame = bytes(buf[:i])        # bytes up to CRLF
            buf = buf[i + 1:]             # remove frame + CRLF from buffer

            req = frame.decode("utf-8", "ignore")
            resp = build_response(req)
            if resp is not None:
                uart.write(resp)

        # timeout for a *partial* frame (buffer has some bytes but no CRLF)
        if buf:
            if asyncio.ticks_diff(time.ticks_ms(), last_rx_ms) > request_timeout_ms:
                log.debug(f"Partial-frame timeout, dropping {len(buf)} bytes")
                #buf.clear()
                buf = bytearray()
                uart.write(b"ERR timeout\r\n")