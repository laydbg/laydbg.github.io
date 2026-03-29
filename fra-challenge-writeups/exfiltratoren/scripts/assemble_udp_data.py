import json

chunk_data = {}

def decode_hex(hex_str):
    return bytes.fromhex(hex_str)

with open("udp_stream_1.txt", "r") as f:
    for line in f:
        try:
            objs = json.loads(f"[{line.replace('}{', '},{')}]")  # Handles multiple JSON objects in one line
            for obj in objs:
                if 'chunk' in obj and 'data' in obj['chunk']:
                    ix = obj['chunk']['ix']
                    raw = obj['chunk']['data']
                    decoded_data = bytes.fromhex(raw)
                    chunk_data[ix] = decoded_data
        except json.JSONDecodeError:
            continue

with open("top_secret_encrypted", "wb") as out_file:
    for ix in sorted(chunk_data):
        data = chunk_data[ix]
        out_file.write(data)

