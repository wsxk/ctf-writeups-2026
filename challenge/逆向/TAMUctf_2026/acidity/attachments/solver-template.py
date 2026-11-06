from pwn import *
import threading
import sys, termios, select, tty

io = remote("streams.tamuctf.com", 443, ssl=True, sni="acidity")

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

interactive(io)