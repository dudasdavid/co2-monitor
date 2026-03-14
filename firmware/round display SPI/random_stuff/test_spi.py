import lvgl as lv
import gc9a01
import lcd_bus
from machine import SPI, Pin
from micropython import const

_WIDTH = const(240)
_HEIGHT = const(240)


_SPI_HOST = const(1)
_SPI_SCK = const(3)
_SPI_MOSI = const(10)
_SPI_MISO = const(0)

_LCD_FREQ = const(80000000)
_LCD_DC = const(18)
_LCD_CS = const(2)
_LCD_RST = const(21)
_LCD_BACKLIGHT = const(42)

_SCL = const(9)
_SDA = const(8)
_TP_FREQ = const(100000)

# Initialize LVGL
lv.init()

print(_SPI_HOST, _SPI_MOSI, _SPI_MISO, _SPI_SCK)
print(type(_SPI_HOST), type(_SPI_MOSI), type(_SPI_MISO), type(_SPI_SCK))

# Initialize the SPI bus
spi_bus = SPI.Bus(
    host = _SPI_HOST,
    mosi = _SPI_MOSI,
    miso = _SPI_MISO,
    sck = _SPI_SCK
)

# Initialize the display bus
display_bus = lcd_bus.SPIBus(
    spi_bus = spi_bus,
    dc = _LCD_DC,
    cs = _LCD_CS,
    freq=_LCD_FREQ 
)

_BUFFER_SIZE = const(57600)
fb1 = display_bus.allocate_framebuffer(_BUFFER_SIZE, lcd_bus.MEMORY_INTERNAL | lcd_bus.MEMORY_DMA)
fb2 = display_bus.allocate_framebuffer(_BUFFER_SIZE, lcd_bus.MEMORY_INTERNAL | lcd_bus.MEMORY_DMA)

# Initialize the GC9A01 display driver
display = gc9a01.GC9A01(
    data_bus = display_bus,
    frame_buffer1=fb1,
    frame_buffer2=fb2,
    display_width = _WIDTH,
    display_height = _HEIGHT,
    reset_pin = _LCD_RST,
    reset_state = gc9a01.STATE_LOW,
    power_on_state = gc9a01.STATE_HIGH,
    backlight_pin=_LCD_BACKLIGHT,
    offset_x=0,
    offset_y=0,
    color_space=lv.COLOR_FORMAT.RGB565,
    rgb565_byte_swap=True
)


# Initialize display
display.set_power(True)
display.init()
display.set_backlight(100)

import i2c  # NOQA
import task_handler  # NOQA
import cst816s

i2c_bus = i2c.I2C.Bus(host=0, scl=_SCL, sda=_SDA, freq=_TP_FREQ, use_locks=False)
touch_dev = i2c.I2C.Device(bus=i2c_bus, dev_id=cst816s.I2C_ADDR, reg_bits=cst816s.BITS)

indev = cst816s.CST816S(touch_dev)

if not indev.is_calibrated:
    display.set_backlight(100)
    indev.calibrate()

display.set_backlight(10)

th = task_handler.TaskHandler()

scrn = lv.screen_active()
scrn.set_style_bg_color(lv.color_hex(0x000000), 0)

slider = lv.slider(scrn)
slider.set_size(180, 50)
slider.center()

label = lv.label(scrn)
label.set_text('HELLO WORLD!')
label.align(lv.ALIGN.CENTER, 0, -50)

'''
Adjusting backlight:
>>> a=Pin(42, Pin.OUT)
>>> a.off()
>>> a.on()
>>> from machine import Pin, PWM
>>> pwm = PWM(Pin(42))
>>> pwm.freq(1000)
>>> pwm.duty_u16(32768)
>>> pwm.duty_u16(1)
>>> pwm.duty_u16(10)
>>> pwm.duty_u16(100)
>>> pwm.duty_u16(1000)
>>> pwm.duty_u16(10000)
>>> pwm.duty_u16(1000)
>>> pwm.duty_u16(60000)
'''