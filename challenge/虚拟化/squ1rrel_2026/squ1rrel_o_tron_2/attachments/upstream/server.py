#!/usr/bin/env python3
import os
import random
import socket
import socketserver
import string
import sys
import time


def mix(s: str) -> str:
  raise NotImplementedError


FLAG      = os.environ.get("FLAG", "squ1rrel{TEST_FLAG}")
ROUNDS    = int(os.environ.get("ROUNDS", "20000"))
CHAL_LEN  = int(os.environ.get("CHAL_LEN", "8"))
INIT_PREV = os.environ.get("INIT_PREV", "0000")
TIMEOUT   = int(os.environ.get("TIMEOUT", "5"))
LISTEN    = ("0.0.0.0", int(os.environ.get("PORT", "1987")))

ALPHABET  = string.ascii_lowercase + string.digits


def recv_line(sock, deadline, max_len=64):
  data = b""
  while not data.endswith(b"\n"):
    if len(data) > max_len:
      raise ValueError("line too long")
    remaining = deadline - time.monotonic()
    if remaining <= 0:
      raise socket.timeout
    sock.settimeout(remaining)
    chunk = sock.recv(1)
    if not chunk:
      raise ConnectionResetError
    data += chunk
  return data.rstrip(b"\r\n").decode("ascii", errors="replace")


class Handler(socketserver.BaseRequestHandler):
  def handle(self):
    sock = self.request

    challenges = ["".join(random.choice(ALPHABET) for _ in range(CHAL_LEN))
                  for _ in range(ROUNDS)]

    deadline = time.monotonic() + TIMEOUT
    try:
      sock.settimeout(TIMEOUT)
      sock.sendall(
          b"squ1rrel-o-tron-2 oracle\n"
          + f"{ROUNDS} challenges follow, terminated by END.\n".encode()
          + f"a_i = mix(a_(i-1) + c_i); a_(-1) = \"{INIT_PREV}\"; one hex line per challenge.\n".encode()
          + f"you have {TIMEOUT} seconds total.\n".encode()
          + b"--- CHALLENGES ---\n"
          + ("\n".join(challenges) + "\n").encode()
          + b"--- END ---\n"
      )

      prev = INIT_PREV
      for i, c in enumerate(challenges):
        prev = mix(prev + c)
        try:
          line = recv_line(sock, deadline).strip().lower()
        except (ConnectionResetError, socket.timeout, ValueError):
          return
        if line != prev:
          sock.sendall(f"wrong on challenge {i}\n".encode())
          return
      if time.monotonic() > deadline:
        return

      sock.sendall(f"all {ROUNDS} correct\n{FLAG}\n".encode())

    except (BrokenPipeError, ConnectionResetError, socket.timeout):
      return


class ReusingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
  allow_reuse_address = True
  daemon_threads      = True


def main():
  print(f"squ1rrel-o-tron-2 oracle listening on {LISTEN[0]}:{LISTEN[1]}  "
        f"(rounds={ROUNDS}, timeout={TIMEOUT}s)", flush=True)
  with ReusingServer(LISTEN, Handler) as srv:
    srv.serve_forever()


if __name__ == "__main__":
  sys.exit(main() or 0)
