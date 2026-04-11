import struct
import os
from pwn import *

HOST = "undutmaning-manifest.chals.io"

# Read keys from binary
script_dir = os.path.dirname(os.path.abspath(__file__))
binary_path = os.path.join(script_dir, "server")
binary = open(binary_path, "rb").read()
SECRET_KEY = binary[0x6278 : 0x6278 + 8]
MANIFEST_OBF = binary[0x5020 : 0x5020 + 0x1250]


# Crypto helpers
def rotate_right(val, n):
    val &= 0xFF
    n &= 7
    return ((val >> n) | (val << (8 - n))) & 0xFF


def rotate_left(val, n):
    val &= 0xFF
    n &= 7
    return ((val << n) | (val >> (8 - n))) & 0xFF


def bitwise_not(x):
    return (~x) & 0xFF


# Server function copies
def transform_challenge(challenge):
    result = bytearray(8)
    for i in range(8):
        x = SECRET_KEY[i] ^ challenge[i]
        x = rotate_left(x, i % 3)
        if i % 2:
            x = bitwise_not(x)
        result[i] = x
    return result


def apply_keystream_challenge_manifest(data, manifest, manifest_pos, challenge):
    result = bytearray(data)
    for i in range(len(data)):
        m = manifest[(i + manifest_pos[0]) % len(manifest)]
        result[i] ^= m
        result[i] ^= challenge[i % 8]
    manifest_pos[0] += len(data)
    return result


def reconstruct_manifest():
    manifest = bytearray(0x1250)
    for i in range(0x1250):
        value = MANIFEST_OBF[i]
        value ^= i * 0x1F
        value = rotate_right(value, i % 7)
        value ^= 0xA5
        manifest[i] = value
    return manifest


def send_packet(s, ptype, data):
    s.send(struct.pack(">HH", ptype, len(data)) + data)


def recv_packet(s):
    buf = s.recvn(4)
    ptype, plen = struct.unpack(">HH", buf)
    data = s.recvn(plen) if plen > 0 else b""
    return ptype, data


# Main
RESPONSE = 2
COMMAND = 0x100

manifest = reconstruct_manifest()
manifest_pos = [0]

# Connect and authenticate
s = remote(HOST, 443, ssl=True, sni=HOST)

banner = s.recvuntil(b"\n")

_, challenge = recv_packet(s)

response = transform_challenge(challenge)
send_packet(s, RESPONSE, response)

_, authenticated = recv_packet(s)

# LIST
send_packet(
    s,
    COMMAND,
    apply_keystream_challenge_manifest(b"LIST", manifest, manifest_pos, challenge),
)
_, enc = recv_packet(s)
files = apply_keystream_challenge_manifest(enc, manifest, manifest_pos, challenge)
print(f"> Files:\n{files.decode()}")

# REQUESTs
for file in files.decode().strip().split("\n"):
    file = file.strip()
    print(f"> File: {file}")
    send_packet(
        s,
        COMMAND,
        apply_keystream_challenge_manifest(
            f"REQUEST {file}".encode(), manifest, manifest_pos, challenge
        ),
    )
    _, enc = recv_packet(s)
    content = apply_keystream_challenge_manifest(enc, manifest, manifest_pos, challenge)
    print(content.decode())

s.close()
