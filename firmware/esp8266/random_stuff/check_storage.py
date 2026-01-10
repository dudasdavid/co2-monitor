import os
import time
 
# Get file system stats
stats = os.statvfs('/flash')

block_size = stats[0]
total_blocks = stats[2]
free_blocks = stats[3]

total_space = block_size * total_blocks
free_space = block_size * free_blocks
used_space = total_space - free_space

print("Total space:", total_space / 1024, "kB")
print("Used space:", used_space / 1024, "kB")
print("Free space:", free_space / 1024, "kB")

print(os.uname())


