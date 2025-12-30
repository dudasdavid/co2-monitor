from machine import Pin, I2C
import uasyncio as asyncio
import time

'''
# Hardware I2C1 on PB8 (SCL) / PB9 (SDA)
i2c = I2C(1, scl=Pin('D15'), sda=Pin('D14'), freq=100_000)
print(i2c.scan())  # list device addresses found
'''

# I2C1 uses PB8=D15 (SCL) / PB9=D14 (SDA) on STM32F746 builds
i2c1=I2C(1, freq=100000)
devices = i2c1.scan()

expected_ids = [16, 56, 83, 98, 104, 118]
expected_names = ["VEML7700", "AHTx0", "ENS160", "SCD4x", "DS3231", "BMP280"]

for id in devices:
    
    if id in expected_ids:
        exp_idx = expected_ids.index(id)
        expected_ids.pop(exp_idx)
        print("[SUCCESS]", expected_names.pop(exp_idx), "was found at", id, hex(id))
    else:    
        print("[ERROR] Unexpected i2c address at", id, hex(id))

for i in range(0, len(expected_ids)):
    print("[ERROR]", expected_names[i], "was not found at address:", expected_ids[i], hex(expected_ids[i]))