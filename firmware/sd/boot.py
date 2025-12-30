# boot.py -- run on boot-up
print("boot.py is running from SD card")

import os

# Try to switch working dir to flash so relative paths/imports behave
try:
    os.chdir("/flash")
except:
    pass

# Run the flash boot/main explicitly
try:
    exec(open("/flash/boot.py").read(), {})
except:
    pass

try:
    exec(open("/flash/main.py").read(), {})
except:
    pass