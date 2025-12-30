import os
import pyb

sd = pyb.SDCard()  # or your SD block device (SPI SD driver object)
# Unmount first if already mounted:
try:
    os.umount("/sd")
except:
    pass

os.VfsFat.mkfs(sd)           # <-- makes a FAT filesystem on the card
os.mount(sd, "/sd")
print(os.listdir("/sd"))