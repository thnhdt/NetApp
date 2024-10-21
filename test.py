import os
import hashlib
import math

arr = [b'a', b'a', b'a',b'a',b'a',b'a',b'a']
idx = [6,3,0,1,2,5,4]
for i in idx:
    with open("./a.txt", "r+b") as file:
        file.seek(i)
        file.write(arr[i])