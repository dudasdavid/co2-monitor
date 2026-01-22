import uasyncio as asyncio
from machine import Pin, PWM

# ---- Global variables ----
import shared_variables as var

async def led_task(period = 1.0):
    #Init
    pwm = PWM(Pin(2))
    pwm.freq(500)
    #pwm.duty(1023)

    duty = 1023
    step = 32
    direction = 1

    #Run
    while True:
        
        pwm.duty(duty)

        duty += direction * step

        if duty >= 1023:
            duty = 1023
            direction = -1
        elif duty <= 500:
            duty = 500
            direction = 1

        await asyncio.sleep(period)

if __name__ == "__main__":
    print("TESTING SINGLE TASK!")
    asyncio.run(led_task(0.1))