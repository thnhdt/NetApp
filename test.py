import os
import hashlib
import math
shared_file_path = './a.txt'  # Replace with your actual file path
piece_length = 256
total_length = 0
piece_hashes = []

# Simulating a single file of 500 bytes for demonstration
lengths = [500, 100, 100, 100]
pieceBoundaries= [0]
for length in lengths:
    piece_no = math.ceil(length / piece_length)
    pieceBoundaries.append(pieceBoundaries[-1] + piece_no)
pieceBoundaries.pop(0)

s = '000'
index = 3
new_char = "1"
new_s = s[:index] + new_char + s[index+1:]
print(new_s)