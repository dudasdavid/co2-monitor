import uasyncio as asyncio
from machine import UART, Pin
from logger import Logger

# ---- Global variables ----
import shared_variables as var

async def serial_task(period = 1.0):
    #Init
    log = Logger("uart", debug_enabled=False)
    
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

    # ---- Simple request->response handler ----
    # You can replace this with your own protocol.
    def build_response(req: str) -> bytes:
        r = req.strip()  # strip whitespace + CR/LF

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
                    return b"WiFi is NOT connected\r\n"

        if r == "AP_STATUS?":
            if var.ap_enabled:
                return b"AP enabled | 192.168.4.1\r\n"
            else:
                if var.ap_request:
                    return b"AP requested\r\n"
                else:
                    return b"AP disabled\r\n"

        if r == "TIME?":
            if ntp_time_synchronized:
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
            var.pm2_5 = float(data_array[1])
            var.pm10 = float(data_array[2])
            var.tvoc = float(data_array[3])
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

        # default: echo
        return "ECHO {}\r\n".format(r).encode()

    # ---- Main loop ----
    buf = bytearray()

    #Run
    while True:
        # 1) wait for incoming traffic
        while not uart.any():
            await asyncio.sleep(period)

        # 2) read until \r\n (single "request line")
        buf.clear()
        start_ms = asyncio.ticks_ms()

        while True:
            # timeout protection
            if asyncio.ticks_diff(asyncio.ticks_ms(), start_ms) > request_timeout_ms:
                log.debug("Request timeout, clearing partial buffer (len={})".format(len(buf)))
                buf.clear()
                # Optional: send a timeout response
                uart.write(b"ERR timeout\r\n")
                break

            if uart.any():
                chunk = uart.read()
                if chunk:
                    # append, with max length protection
                    if len(buf) + len(chunk) > max_request_len:
                        log.debug("Request too long, dropping (>{})".format(max_request_len))
                        buf.clear()
                        uart.write(b"ERR too_long\r\n")
                        # drain whatever is still coming for this burst
                        while uart.any():
                            _ = uart.read()
                            await asyncio.sleep(0)
                        break

                    buf.extend(chunk)

                    # terminator found?
                    if len(buf) >= 2 and buf[-2:] == b"\r\n":
                        req = buf[:-2].decode("utf-8", "ignore")  # exclude CRLF
                        # 3) build + send response
                        resp = build_response(req)
                        if resp is not None:
                            uart.write(resp)
                        break
            else:
                await asyncio.sleep(period)