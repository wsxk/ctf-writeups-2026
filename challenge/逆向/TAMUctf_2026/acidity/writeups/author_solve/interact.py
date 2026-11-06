from pwn import remote, sleep, process
import threading
import sys, termios, select, tty

FRAME_TIME_MS = 100
SLEEP_TIME = FRAME_TIME_MS / 1000
correct = b'bbbcbbbccbbefb'

# r = remote('localhost', 4716)
r = process(['../build/acidity'])

total_frames = 0
rain = []
def wait_for_frame(r):
    global total_frames
    total_frames += 1
    frame = r.recvuntil(b'[q] quit\r\n').decode()
    print(frame)
    lines = frame.splitlines()[:2]
    if 'RNG' in lines[0]:
        rain.append(lines[1][18])
    return frame


r.send(b'a')
frame = wait_for_frame(r)
frame = wait_for_frame(r)
frame = wait_for_frame(r)

for c in correct:
    r.send(bytes([c]))
    for _ in range(4):
        frame = wait_for_frame(r)

# print(rain)
for _ in range(39):
    wait_for_frame(r)

r.send(b'd')

def interactive(r):
    def recv_thread(r):
        while True:
            try:
                data = r.recv(timeout=0.05)
                if data:
                    print(data.decode(), end='', flush=True)
            except EOFError:
                break
            except Exception:
                pass
    
    t = threading.Thread(target=recv_thread, args=(r,))
    t.daemon = True
    t.start()

    # non-blocking input loop
    orig = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())
        while True:
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                ch = sys.stdin.read(1)
                r.send(ch.encode())
            sleep(0.05)
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, orig)

# interactive(r)
print(r.recvall().decode())
print(total_frames)
