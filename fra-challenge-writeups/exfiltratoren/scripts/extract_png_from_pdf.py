#!/usr/bin/env python3

# pip requirements: base45 numpy pyzbar pdf2image pillow
import base45
import numpy as np
from pyzbar.pyzbar import decode
from pdf2image import convert_from_path
from PIL import Image

images = convert_from_path("presentkort.pdf")
qr_data = decode(np.array(images[0]))[0].data.decode('utf-8')

decoded_bytes = base45.b45decode(qr_data)
with open("qr_decoded.png", 'wb') as f:
    f.write(decoded_bytes)