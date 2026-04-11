import json, sys, os
from collections import deque
from PIL import Image
import numpy as np
from pwn import *

HOST = "undutmaning-deep.chals.io"
GRID = 31
START = (1, 1)
BATTERY = (29, 29)

# Parse maze from image
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAP_PATH = os.path.join(SCRIPT_DIR, "lab-map.png")


def load_grid(path):
    img = Image.open(path).convert("RGB")
    arr = np.array(img)
    cell = img.size[0] / GRID
    grid = []
    for row in range(GRID):
        r = []
        for col in range(GRID):
            cx = int((col + 0.5) * cell)
            cy = int((row + 0.5) * cell)
            px = arr[cy, cx]
            brightness = int(px[0]) + int(px[1]) + int(px[2])
            r.append(0 if brightness < 200 else 1)
        grid.append(r)
    grid[START[0]][START[1]] = 1
    grid[BATTERY[0]][BATTERY[1]] = 1
    return grid


GRID_MAP = load_grid(MAP_PATH)

# BFS avoiding sharks
DIRS = [(-1, 0, "N"), (1, 0, "S"), (0, 1, "Ö"), (0, -1, "V")]


def bfs(start, end, sharks):
    shark_set = set(tuple(s) for s in sharks)
    q = deque([(start, [])])
    visited = {start}
    while q:
        (r, c), path = q.popleft()
        if (r, c) == end:
            return path
        for dr, dc, d in DIRS:
            nr, nc = r + dr, c + dc
            if (
                0 <= nr < GRID
                and 0 <= nc < GRID
                and GRID_MAP[nr][nc] == 1
                and (nr, nc) not in visited
                and (nr, nc) not in shark_set
            ):
                visited.add((nr, nc))
                q.append(((nr, nc), path + [d]))
    return None


# Wait for shark update resulting in a valid path, return path
def wait_for_opening(s, start, end):
    while True:
        line = s.recvline(timeout=30).decode("utf-8", errors="replace").strip()
        print(line)

        try:
            sharks = json.loads(line).get("sharks")
            path = bfs(start, end, sharks)
            if path:
                return path
        except:
            continue


s = remote(HOST, 443, ssl=True, sni=HOST)

# Get to battery
path = wait_for_opening(s, START, BATTERY)
to_send = "".join(path)
print(">", to_send)
s.sendline(to_send.encode())

# Return
path = wait_for_opening(s, BATTERY, START)
to_send = "".join(path)
print(">", to_send)
s.sendline(to_send.encode())

while True:
    try:
        line = s.recvline(timeout=15).decode("utf-8", errors="replace").strip()
        print(line)
    except EOFError:
        break
s.close()
