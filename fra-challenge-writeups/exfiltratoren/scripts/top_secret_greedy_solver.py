import time
import random
import numpy as np
from PIL import Image

INPUT_PATH = "top_secret.png"
OUTPUT_PATH = "restored.png"
TILE_SIZE = 8
GRID_COLS = 128
PUZZLE_ROWS = 2
NUM_PUZZLES = 64
ALPHA_START = 255

ALPHA_W = 0.6
BETA_W = 0.4


def load_and_group_tiles(path):
    img = Image.open(path).convert("RGBA")
    arr = np.array(img, dtype=np.float32)
    H, W = arr.shape[:2]
    tile_rows = H // TILE_SIZE
    tile_cols = W // TILE_SIZE

    print(f"Loaded {path}: {W}x{H}px ({tile_cols}x{tile_rows} tiles)")

    groups = {}
    for tr in range(tile_rows):
        for tc in range(tile_cols):
            r0 = tr * TILE_SIZE
            c0 = tc * TILE_SIZE
            tile = arr[r0 : r0 + TILE_SIZE, c0 : c0 + TILE_SIZE]
            alpha = int(tile[TILE_SIZE // 2, TILE_SIZE // 2, 3])
            rgb = tile[:, :, :3].copy()
            groups.setdefault(alpha, []).append(rgb)
    return groups


def make_output_canvas(w, h):
    return np.zeros((h, w, 4), dtype=np.float32)


def write_puzzle_to_canvas(canvas, puzzle_idx, arrangement, tiles):
    base = puzzle_idx * PUZZLE_ROWS * TILE_SIZE
    for col_idx, (t, b) in enumerate(arrangement):
        c0 = col_idx * TILE_SIZE
        canvas[base : base + TILE_SIZE, c0 : c0 + TILE_SIZE, :3] = tiles[t]
        canvas[base + TILE_SIZE : base + 2 * TILE_SIZE, c0 : c0 + TILE_SIZE, :3] = (
            tiles[b]
        )
        canvas[base : base + 2 * TILE_SIZE, c0 : c0 + TILE_SIZE, 3] = 255


def get_edges(tile):
    return tile[0], tile[-1], tile[:, 0], tile[:, -1]


def gradient_1d(a):
    return np.diff(a, axis=0, append=a[-1:])


def edge_score(a, b):
    colour = np.mean((a - b) ** 2)
    grad = np.mean((gradient_1d(a) - gradient_1d(b)) ** 2)
    return float(ALPHA_W * colour + BETA_W * grad)


def build_cost_tables(tiles):
    n = len(tiles)
    edges = [get_edges(t) for t in tiles]
    v_cost = np.full((n, n), np.inf)
    h_cost = np.full((n, n), np.inf)
    for i in range(n):
        ti, bi, li, ri = edges[i]
        for j in range(n):
            if i == j:
                continue
            tj, _, lj, _ = edges[j]
            v_cost[i, j] = edge_score(bi, tj)
            h_cost[i, j] = edge_score(ri, lj)
    return v_cost, h_cost


def greedy_pairing(v_cost):
    n = v_cost.shape[0]
    candidates = []
    for i in range(n):
        for j in range(i + 1, n):
            if v_cost[i, j] <= v_cost[j, i]:
                candidates.append((v_cost[i, j], i, j))
            else:
                candidates.append((v_cost[j, i], j, i))
    candidates.sort(key=lambda x: x[0])

    used = set()
    pairs = []
    for _, t, b in candidates:
        if t not in used and b not in used:
            pairs.append([t, b])
            used.add(t)
            used.add(b)
        if len(pairs) == GRID_COLS:
            break
    return pairs


def build_column_cost_matrix(pairs, h_cost):
    m = len(pairs)
    mat = np.zeros((m, m), dtype=np.float32)
    for i in range(m):
        t1, b1 = pairs[i]
        for j in range(m):
            t2, b2 = pairs[j]
            mat[i, j] = h_cost[t1, t2] + h_cost[b1, b2]
    return mat


def bidirectional_greedy_order(col_cost_mat):
    remaining = list(range(col_cost_mat.shape[0]))
    start = random.choice(remaining)
    path = [start]
    remaining.remove(start)

    while remaining:
        left = path[0]
        right = path[-1]
        best_j = None
        best_c = float("inf")
        prepend = False

        for j in remaining:
            c_left = col_cost_mat[j, left]  # cost if prepend
            c_right = col_cost_mat[right, j]  # cost if append
            if c_left < best_c:
                best_c = c_left
                best_j = j
                prepend = True
            if c_right < best_c:
                best_c = c_right
                best_j = j
                prepend = False

        if prepend:
            path = [best_j] + path
        else:
            path.append(best_j)
        remaining.remove(best_j)

    return path


def solve_puzzle(tiles):
    v_cost, h_cost = build_cost_tables(tiles)
    pairs = greedy_pairing(v_cost)
    order = bidirectional_greedy_order(build_column_cost_matrix(pairs, h_cost))
    return [pairs[i] for i in order]


def main():
    random.seed(42)

    groups = load_and_group_tiles(INPUT_PATH)
    out_h = NUM_PUZZLES * PUZZLE_ROWS * TILE_SIZE
    out_w = GRID_COLS * TILE_SIZE
    canvas = make_output_canvas(out_w, out_h)

    for puzzle_idx in range(NUM_PUZZLES):
        alpha_val = ALPHA_START - puzzle_idx
        tiles = groups.get(alpha_val)
        if tiles is None:
            continue
        print(f"Puzzle {puzzle_idx + 1:>2d}/{NUM_PUZZLES} alpha={alpha_val}")
        arrangement = solve_puzzle(tiles)
        write_puzzle_to_canvas(canvas, puzzle_idx, arrangement, tiles)

    Image.fromarray(canvas.astype(np.uint8), mode="RGBA").save(OUTPUT_PATH)


if __name__ == "__main__":
    main()
