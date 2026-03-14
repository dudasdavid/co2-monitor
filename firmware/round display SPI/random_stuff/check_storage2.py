from machine import SPI, SDCard
import vfs, os
import time
 
# Get file system stats
stats = os.statvfs('/')

block_size = stats[0]
total_blocks = stats[2]
free_blocks = stats[3]

total_space = block_size * total_blocks
free_space = block_size * free_blocks
used_space = total_space - free_space

print("Total space:", total_space / 1024, "kB")
print("Used space:", used_space / 1024, "kB")
print("Free space:", free_space / 1024, "kB")

# Mount SD card

spi_bus = SPI.Bus(
    host=2,
    miso=48, 
    mosi=47,
    sck=41
)

sd = SDCard(
    spi_bus=spi_bus,
    cs=40,
    freq=1000000
)

# If we need to format the SD card
#os.VfsFat.mkfs(sd)

vfs.mount(sd, "/sd")
print('SD card mounted, ls:')
print(os.listdir('/sd'))

# Get file system stats
stats = os.statvfs('/sd')

block_size = stats[0]
total_blocks = stats[2]
free_blocks = stats[3]

total_space = block_size * total_blocks
free_space = block_size * free_blocks
used_space = total_space - free_space

print("Total space:", total_space / 1024, "kB")
print("Used space:", used_space / 1024, "kB")
print("Free space:", free_space / 1024, "kB")

# Check RAM too

import gc
gc.collect()
free = gc.mem_free()
used = gc.mem_alloc()
total = free + used

print("Total RAM:", total/1024, "kB")
print("Used RAM:", used/1024, "kB")
print("Free RAM:", free/1024, "kB")


