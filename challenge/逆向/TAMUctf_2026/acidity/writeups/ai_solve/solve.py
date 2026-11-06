from pwn import *
import threading
from queue import SimpleQueue, Empty
import sys

HOST = "localhost"
PORT = 4716

# io = remote(HOST, PORT)
io = process("./build/acidity")

tick_q = SimpleQueue()
done = threading.Event()
board_q = SimpleQueue()

def xorshift64star(key, state):
    mask = (1 << 64) - 1
    s = (((key & 0xff) << 32) | (key & 0xff)) ^ state
    s = (s ^ ((s << 12) & mask)) & mask
    s = (s ^ (s >> 25)) & mask
    s = (s ^ ((s << 27) & mask)) & mask
    state = s
    out = (state * 0xf337) & mask
    return out, state

def key_for_column(state, col):
    for k in range(256):
        out, next_state = xorshift64star(k, state)
        if (out >> col) & 1:
            return k, next_state
    return 0, state

def recv_loop():
    buf = ""
    while not done.is_set():
        try:
            data = io.recv(timeout=0.1)
        except EOFError:
            done.set()
            break
        if not data:
            continue
        s = data.decode(errors="ignore")
        sys.stdout.write(s)
        sys.stdout.flush()
        if "Congratulations!" in s:
            done.set()
        buf += s
        while True:
            idx = buf.find("Move:")
            if idx == -1:
                if len(buf) > 64:
                    buf = buf[-64:]
                break
            frame = buf[:idx]
            lines = [ln for ln in frame.splitlines() if ln]
            if len(lines) >= 25:
                board = lines[-25:]
                if all(len(row) >= 35 for row in board):
                    board_q.put(board)
            tick_q.put(1)
            buf = buf[idx + 5:]

t = threading.Thread(target=recv_loop, daemon=True)
t.start()

state = 0xf10c70deadbeef00
col = 17
tick = 0
pending_key = 0
phase = "move_left"
ready = False
ready_tick = 1000

while not done.is_set():
    try:
        tick_q.get(timeout=0.1)
    except Empty:
        continue
    tick += 1
    if tick % 4 == 0:
        _, state = xorshift64star(pending_key, state)
    if tick % 4 == 3:
        pending_key, _ = key_for_column(state, col)
        io.send(bytes([pending_key]))
    try:
        board = board_q.get_nowait()
        blocks = 0
        for r in range(12, 24):
            if board[r][col] == "#":
                blocks += 1
        ready = blocks <= 3
        if ready and ready_tick == 1000:
            ready_tick = tick
    except Empty:
        pass
    if tick % 4 == 1:
        if phase == "move_left":
            io.send(b"a")
            phase = "wait"
    print(f'tick {tick}, blocks: {blocks}, ready: {ready}, phase: {phase}, ready_tick: {ready_tick}')
    if phase == "wait" and ready:
        phase = "move_right"
    elif phase == "move_right" and tick >= ready_tick + 12:
        io.send(b"d")
        phase = "done"

t.join()
print(f'done in {tick} ticks')