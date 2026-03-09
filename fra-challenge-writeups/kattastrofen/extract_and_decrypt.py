import base64
import re

inputpath = "dnscat_exfil_data"
outputpath = "exfil.tar"
key = base64.b64decode("P1yq59jxFvIGgyebMmzgQIx6f/ng0fmK+N5+kDdBcgU=") # From 'kitten-3.jpg'

with open(inputpath, "rb") as f:
    raw = f.read()

file_data = re.search(b"(?<=(BEGIN DATA)).+?(?=(END DATA))", raw.replace(b'\n', b'')).group()
file_data = base64.b64decode(file_data)

def xor_decrypt(data, key):
    longkey = (key * (len(data)//len(key) + 1))[:len(data)]
    return bytes(a^b for a, b in zip(data, longkey, strict=True))

dec = xor_decrypt(file_data, key)

with open(outputpath, "wb") as out:
    out.write(dec)

