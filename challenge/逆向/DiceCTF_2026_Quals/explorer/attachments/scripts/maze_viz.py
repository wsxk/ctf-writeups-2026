#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
from collections import deque
from typing import List, Sequence, Tuple

NORTH = 0
EAST = 1
SOUTH = 2
WEST = 3
UP = 4
DOWN = 5


def u32(x: int) -> int:
    return x & 0xFFFFFFFF


def next_rand(seed: int) -> Tuple[int, int]:
    x = u32(seed)
    x ^= u32(x << 13)
    x = u32(x)
    x ^= x >> 17
    x = u32(x)
    x ^= u32(x << 5)
    x = u32(x)
    return x, x


def opposite(d: int) -> int:
    return [SOUTH, WEST, NORTH, EAST, DOWN, UP][d]


def idx_of(x: int, y: int, z: int, sx: int, sy: int) -> int:
    return (z * sy + y) * sx + x


def xyz_of(idx: int, sx: int, sy: int) -> Tuple[int, int, int]:
    plane = sx * sy
    z = idx // plane
    rem = idx % plane
    y = rem // sx
    x = rem % sx
    return x, y, z


def neighbor(idx: int, d: int, sx: int, sy: int, sz: int) -> int | None:
    x, y, z = xyz_of(idx, sx, sy)
    plane = sx * sy

    if d == NORTH and y > 0:
        return idx - sx
    if d == EAST and x + 1 < sx:
        return idx + 1
    if d == SOUTH and y + 1 < sy:
        return idx + sx
    if d == WEST and x > 0:
        return idx - 1
    if d == UP and z + 1 < sz:
        return idx + plane
    if d == DOWN and z > 0:
        return idx - plane
    return None


def carve_maze(seed: int, sx: int, sy: int, sz: int) -> List[int]:
    count = sx * sy * sz
    exits = [0] * count
    visited = [False] * count
    stack = [0]
    visited[0] = True

    rng = u32(seed ^ 0x9E37_79B9)

    while stack:
        cur = stack[-1]
        nidx: List[int] = []
        ndir: List[int] = []

        for d in range(6):
            to = neighbor(cur, d, sx, sy, sz)
            if to is None or visited[to]:
                continue
            nidx.append(to)
            ndir.append(d)

        if not nidx:
            stack.pop()
            continue

        rng, rnd = next_rand(rng)
        pick = rnd % len(nidx)
        to = nidx[pick]
        d = ndir[pick]

        exits[cur] |= 1 << d
        exits[to] |= 1 << opposite(d)

        visited[to] = True
        stack.append(to)

    return exits


def find_goal_path(exits: Sequence[int], sx: int, sy: int, sz: int) -> List[bool]:
    count = sx * sy * sz
    goal = count - 1

    parent = [-1] * count
    vis = [False] * count
    q: deque[int] = deque([0])
    vis[0] = True

    while q:
        cur = q.popleft()
        if cur == goal:
            break
        for d in range(6):
            if (exits[cur] & (1 << d)) == 0:
                continue
            to = neighbor(cur, d, sx, sy, sz)
            if to is None or vis[to]:
                continue
            vis[to] = True
            parent[to] = cur
            q.append(to)

    on_path = [False] * count
    cur = goal
    while cur != -1:
        on_path[cur] = True
        if cur == 0:
            break
        cur = parent[cur]

    return on_path


def goal_path_indices(exits: Sequence[int], sx: int, sy: int, sz: int) -> List[int]:
    count = sx * sy * sz
    goal = count - 1

    parent = [-1] * count
    vis = [False] * count
    q: deque[int] = deque([0])
    vis[0] = True

    while q:
        cur = q.popleft()
        if cur == goal:
            break
        for d in range(6):
            if (exits[cur] & (1 << d)) == 0:
                continue
            to = neighbor(cur, d, sx, sy, sz)
            if to is None or vis[to]:
                continue
            vis[to] = True
            parent[to] = cur
            q.append(to)

    if not vis[goal]:
        return []

    path: List[int] = []
    cur = goal
    while cur != -1:
        path.append(cur)
        if cur == 0:
            break
        cur = parent[cur]
    path.reverse()
    return path


def dead_end_is_spike(seed: int, idx: int) -> bool:
    x = u32(seed ^ u32(idx * 0x9E37_79B9))
    x ^= x >> 16
    x = u32(x * 0x7FEB_352D)
    x ^= x >> 15
    x = u32(x * 0x846C_A68B)
    x ^= x >> 16
    return (x & 1) == 0


def node_types(seed: int, exits: Sequence[int], on_path: Sequence[bool]) -> List[str]:
    count = len(exits)
    goal = count - 1
    out = ["none"] * count

    for i in range(count):
        if i == goal:
            out[i] = "goal"
            continue
        if i == 0 or on_path[i]:
            out[i] = "none"
            continue

        degree = (exits[i] & 0x3F).bit_count()
        if degree == 1 and dead_end_is_spike(seed, i):
            out[i] = "spike"

    return out


def parse_seed_dims(text: str) -> Tuple[int, int, int, int]:
    m = re.search(
        r"seed\s*=\s*0x([0-9a-fA-F]+).*?dims\s*=\s*(\d+)\s*[x, ]\s*(\d+)\s*[x, ]\s*(\d+)",
        text,
        flags=re.DOTALL,
    )
    if not m:
        raise ValueError("could not parse 'seed=0x... dims=AxBxC' from input")

    seed = int(m.group(1), 16)
    sx = int(m.group(2))
    sy = int(m.group(3))
    sz = int(m.group(4))
    return seed, sx, sy, sz


def cell_char(i: int, exits: Sequence[int], kinds: Sequence[str], sx: int, sy: int) -> str:
    x, y, z = xyz_of(i, sx, sy)
    if x == 0 and y == 0 and z == 0:
        return "S"
    if kinds[i] == "goal":
        return "G"
    if kinds[i] == "spike":
        return "X"

    up = (exits[i] & (1 << UP)) != 0
    down = (exits[i] & (1 << DOWN)) != 0
    if up and down:
        return "B"
    if up:
        return "^"
    if down:
        return "v"
    return "."


def render_ascii(exits: Sequence[int], kinds: Sequence[str], sx: int, sy: int, sz: int) -> str:
    lines: List[str] = []

    for z in range(sz):
        lines.append(f"z={z}")
        h = 2 * sy + 1
        w = 2 * sx + 1
        canvas = [["#" for _ in range(w)] for _ in range(h)]

        for y in range(sy):
            for x in range(sx):
                i = idx_of(x, y, z, sx, sy)
                cy = 2 * y + 1
                cx = 2 * x + 1
                canvas[cy][cx] = cell_char(i, exits, kinds, sx, sy)

                if exits[i] & (1 << EAST):
                    canvas[cy][cx + 1] = "-"
                if exits[i] & (1 << SOUTH):
                    canvas[cy + 1][cx] = "|"

        lines.extend("".join(row) for row in canvas)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def maze_edges(exits: Sequence[int], sx: int, sy: int, sz: int) -> List[Tuple[int, int]]:
    edges: List[Tuple[int, int]] = []
    count = sx * sy * sz
    for i in range(count):
        for d in (EAST, SOUTH, UP):
            if (exits[i] & (1 << d)) == 0:
                continue
            to = neighbor(i, d, sx, sy, sz)
            if to is not None:
                edges.append((i, to))
    return edges


def render_matplotlib_3d(
    seed: int, exits: Sequence[int], kinds: Sequence[str], sx: int, sy: int, sz: int, output: str | None
) -> int:
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        print("error: matplotlib is not installed; install python3-matplotlib", file=sys.stderr)
        return 3

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")

    count = sx * sy * sz
    xs: List[int] = []
    ys: List[int] = []
    zs: List[int] = []
    colors: List[str] = []
    sizes: List[int] = []

    for i in range(count):
        x, y, z = xyz_of(i, sx, sy)
        xs.append(x)
        ys.append(y)
        zs.append(z)

        if x == 0 and y == 0 and z == 0:
            colors.append("tab:blue")
            sizes.append(64)
        elif kinds[i] == "goal":
            colors.append("tab:green")
            sizes.append(64)
        elif kinds[i] == "spike":
            colors.append("tab:red")
            sizes.append(36)
        else:
            colors.append("0.55")
            sizes.append(20)

    for a, b in maze_edges(exits, sx, sy, sz):
        axa, aya, aza = xyz_of(a, sx, sy)
        axb, ayb, azb = xyz_of(b, sx, sy)
        ax.plot([axa, axb], [aya, ayb], [aza, azb], color="0.75", linewidth=1.0, alpha=0.9)

    path = goal_path_indices(exits, sx, sy, sz)
    if path:
        px: List[int] = []
        py: List[int] = []
        pz: List[int] = []
        for i in path:
            x, y, z = xyz_of(i, sx, sy)
            px.append(x)
            py.append(y)
            pz.append(z)
        ax.plot(px, py, pz, color="gold", linewidth=3.0, alpha=0.95)

    ax.scatter(xs, ys, zs, c=colors, s=sizes, depthshade=False)
    ax.scatter([0], [0], [0], c=["tab:blue"], s=[100], marker="s", depthshade=False)
    ax.scatter([sx - 1], [sy - 1], [sz - 1], c=["tab:green"], s=[100], marker="*", depthshade=False)

    ax.set_title(f"Challenge maze seed=0x{seed:08x} dims={sx}x{sy}x{sz}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    ax.set_xlim(-0.5, sx - 0.5)
    ax.set_ylim(-0.5, sy - 0.5)
    ax.set_zlim(-0.5, sz - 0.5)
    ax.set_box_aspect((sx, sy, sz))

    if output:
        fig.savefig(output, dpi=200, bbox_inches="tight")
    else:
        plt.show()

    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Visualize challenge maze from seed/dims output")
    ap.add_argument(
        "input",
        nargs="?",
        help="input text containing 'seed=0x... dims=AxBxC'; defaults to stdin",
    )
    ap.add_argument("--plot", action="store_true", help="render a 3D matplotlib plot")
    ap.add_argument(
        "-o",
        "--output",
        help="output file path (.txt for ASCII mode, image path for --plot mode)",
    )
    args = ap.parse_args()

    text = args.input if args.input is not None else sys.stdin.read()

    try:
        seed, sx, sy, sz = parse_seed_dims(text)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    exits = carve_maze(seed, sx, sy, sz)
    on_path = find_goal_path(exits, sx, sy, sz)
    kinds = node_types(seed, exits, on_path)

    if args.plot:
        return render_matplotlib_3d(seed, exits, kinds, sx, sy, sz, args.output)

    out = []
    out.append(f"seed=0x{seed:08x} dims={sx}x{sy}x{sz}")
    out.append("legend: S=start G=goal X=spike .=normal ^=up v=down B=up+down")
    out.append(render_ascii(exits, kinds, sx, sy, sz).rstrip())
    rendered = "\n".join(out) + "\n"

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(rendered)
    else:
        sys.stdout.write(rendered)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
