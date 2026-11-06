#!/usr/bin/env python3
import glob
import http.server
import os
import re
import secrets
import socketserver
import subprocess
import threading
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PACK_NAME = os.getenv("PACK_NAME", "instance")
HTTP_PORT = int(os.getenv("HTTP_PORT", "8000"))
TOKEN_PORT = int(os.getenv("TOKEN_PORT", "31337"))
TOKEN_BYTES = int(os.getenv("TOKEN_BYTES", "16"))
BINARY_FILENAME = os.getenv("BINARY_FILENAME", "another_onion")
TOKEN_PREFIX = "Congratulations! Please submit the following token to get the flag: "


if not re.fullmatch(r"[A-Za-z0-9_]+", PACK_NAME):
    raise RuntimeError("PACK_NAME must match [A-Za-z0-9_]+")
if TOKEN_BYTES < 1:
    raise RuntimeError("TOKEN_BYTES must be >= 1")


def run_checked(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def load_flag() -> str:
    flag = os.getenv("FLAG")
    if flag:
        return flag.strip()
    fallback = ROOT / "flag_real"
    if fallback.exists():
        return fallback.read_text().strip()
    raise RuntimeError("FLAG is not set and flag_real is missing")


def cleanup_instance_artifacts(pack_name: str) -> None:
    suffixes = [
        f"generated_code_{pack_name}.S",
        f"generated_encrypt_{pack_name}.c",
        f"generated_encrypt_{pack_name}",
        f"unpacked_{pack_name}",
        f"dump_{pack_name}.asm",
        f"encryption_log_{pack_name}.txt",
        f"secret_input_{pack_name}",
        f"flag_{pack_name}",
    ]
    for rel in suffixes:
        path = ROOT / rel
        if path.exists():
            path.unlink()
    for pyc_path in glob.glob(str(ROOT / "__pycache__" / f"generated_code_{pack_name}*.pyc")):
        Path(pyc_path).unlink(missing_ok=True)


def build_instance() -> tuple[str, Path]:
    token = secrets.token_hex(TOKEN_BYTES)
    (ROOT / f"flag_{PACK_NAME}").write_text(token)

    run_checked(["python3", "generate.py", PACK_NAME])
    run_checked(["bash", "compile.sh", PACK_NAME])

    binary_path = ROOT / f"packed_{PACK_NAME}"
    if not binary_path.exists():
        raise RuntimeError(f"missing built binary: {binary_path}")

    cleanup_instance_artifacts(PACK_NAME)
    return token, binary_path


class BinaryHandler(http.server.BaseHTTPRequestHandler):
    binary_data: bytes = b""
    filename = BINARY_FILENAME

    def do_GET(self) -> None:  # noqa: N802
        request_path = self.path.split("?", 1)[0]
        if request_path in ("", "/"):
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", f'attachment; filename="{self.filename}"')
            self.send_header("Content-Length", str(len(self.binary_data)))
            self.end_headers()
            self.wfile.write(self.binary_data)
            return

        self.send_response(404)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"not found\n")

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[http] {self.client_address[0]} {fmt % args}", flush=True)


class TokenHandler(socketserver.StreamRequestHandler):
    token = ""
    flag = ""

    def handle(self) -> None:
        self.connection.settimeout(15)
        self.wfile.write(b"token> ")
        data = self.rfile.readline(512)
        if not data:
            return

        submitted = data.strip().decode("utf-8", errors="ignore")
        if submitted.startswith(TOKEN_PREFIX):
            submitted = submitted[len(TOKEN_PREFIX):].strip()
        if secrets.compare_digest(submitted, self.token):
            self.wfile.write((self.flag + "\n").encode())
        else:
            self.wfile.write(b"invalid token\n")


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True


def main() -> None:
    flag = load_flag()
    token, binary_path = build_instance()
    binary_data = binary_path.read_bytes()

    BinaryHandler.binary_data = binary_data
    TokenHandler.token = token
    TokenHandler.flag = flag

    httpd = ThreadedHTTPServer(("0.0.0.0", HTTP_PORT), BinaryHandler)
    tcpd = ThreadedTCPServer(("0.0.0.0", TOKEN_PORT), TokenHandler)

    http_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    tcp_thread = threading.Thread(target=tcpd.serve_forever, daemon=True)
    http_thread.start()
    tcp_thread.start()

    print(f"binary endpoint: http://0.0.0.0:{HTTP_PORT}/", flush=True)
    print(f"token endpoint: 0.0.0.0:{TOKEN_PORT}", flush=True)

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        httpd.shutdown()
        tcpd.shutdown()
        httpd.server_close()
        tcpd.server_close()


if __name__ == "__main__":
    main()
