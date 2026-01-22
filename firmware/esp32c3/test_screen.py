from machine import I2C
import time

i2c=I2C(0, freq=100000, scl=6, sda=5)
i2c.scan()

from drivers import ssd1306

display = ssd1306.SSD1306_I2C(72, 40, i2c)

msg = "192.168.1.250"
x = display.width   # start just off the right edge
y = 0

# 8px per character in this font
msg_w = len(msg) * 8

while True:
    display.fill(0)
    display.text(msg, x, 20, 1)
    display.show()

    x -= 2  # scroll speed (try 1..4)
    if x < -msg_w:
        x = display.width

    time.sleep(0.05)

