#!/usr/bin/env bash
# NDIAS Automotive/IoT CTF — player connection script
# Usage: ./connect.sh <challenge_host> [port]
#
# Requirements: Docker with --cap-add NET_ADMIN support (Linux / Docker Desktop)
set -eu

HOST="${1:?Usage: $0 <challenge_host> [port]}"
PORT="${2:-13337}"
IMAGE="ndias-ctf-player"

# ── check Docker ──────────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
    echo "[!] Docker not found. Please install Docker first." >&2
    exit 1
fi

# ── build image (first time only) ────────────────────────────────────────────
if ! docker image inspect "$IMAGE" &>/dev/null 2>&1; then
    echo "[*] Building player environment (first time only, may take a few minutes)..."

    BUILD_DIR="$(mktemp -d)"
    trap 'rm -rf "$BUILD_DIR"' EXIT

    # ── Dockerfile ───────────────────────────────────────────────────────────
    cat > "$BUILD_DIR/Dockerfile" << 'DOCKERFILE'
FROM ubuntu:24.04

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        bash \
        can-utils \
        curl \
        file \
        git \
        iproute2 \
        iputils-ping \
        less \
        net-tools \
        procps \
        python3 \
        python3-pip \
        tcpdump \
        vim \
        wget \
    && rm -rf /var/lib/apt/lists/*

COPY canproxy.py /opt/player/

CMD ["bash", "-lc", "\
    if ip link add dev vcan0 type vcan 2>/dev/null && ip link set vcan0 up; then \
        echo '[player] kernel vcan0 ready'; \
    else \
        echo '[player] ERROR: could not create vcan0 -- make sure --cap-add NET_ADMIN is set'; \
        exit 1; \
    fi; \
    if [ -n \"${CANPROXY_SERVER_HOST:-}\" ]; then \
        echo \"[player] connecting to ${CANPROXY_SERVER_HOST}:${CANPROXY_SERVER_PORT:-13337}\"; \
        python3 /opt/player/canproxy.py client & \
        sleep 0.5; \
    fi; \
    echo ''; \
    echo '=== NDIAS Automotive/IoT CTF Player ==='; \
    echo '  candump vcan0                          # watch CAN traffic'; \
    echo '  isotprecv -s <SRC> -d <DST> vcan0 &    # ISO-TP receiver'; \
    echo '  printf <HEX> | isotpsend -s <SRC> -d <DST> vcan0   # ISO-TP send'; \
    echo '  python3 -m caringcaribou --help        # UDS scanner (install: pip3 install git+https://github.com/CaringCaribou/caringcaribou.git)'; \
    echo '======================================='; \
    echo ''; \
    exec bash -i"]
DOCKERFILE

    # ── canproxy.py ──────────────────────────────────────────────────────────
    cat > "$BUILD_DIR/canproxy.py" << 'CANPROXY'
#!/usr/bin/env python3
import os
import socket
import threading
import time
import sys

CAN_MTU = 16
CANFD_MTU = 72
FRAME_HEADER_SIZE = 2
VALID_FRAME_SIZES = {CAN_MTU, CANFD_MTU}
DEFAULT_IFACE = "vcan0"
DEFAULT_SERVER_HOST = "0.0.0.0"
DEFAULT_SERVER_PORT = 13337
DEFAULT_RECONNECT_DELAY = 1.0
DEFAULT_RECONNECT_MAX_DELAY = 60.0
DEFAULT_CONNECT_TIMEOUT = 5.0
DEFAULT_HANDSHAKE_TIMEOUT = 5.0
DEFAULT_HEARTBEAT_INTERVAL = 5.0
DEFAULT_HEARTBEAT_TIMEOUT = 15.0
DEFAULT_TCP_IDLE_TIMEOUT = 20.0

CONTROL_FRAME_SIZE = 0
CONTROL_PING = 1
CONTROL_PONG = 2


class HeartbeatTimeout(Exception):
    pass


class ProtocolError(Exception):
    pass


class HandshakeFailed(Exception):
    pass


class FibonacciBackoff:
    def __init__(self, initial_delay: float, max_delay: float) -> None:
        if initial_delay <= 0.0:
            raise ValueError("initial_delay must be greater than 0")
        if max_delay < initial_delay:
            raise ValueError("max_delay must be greater than or equal to initial_delay")
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.reset()
        return

    def reset(self) -> None:
        self.previous_delay = 0.0
        self.current_delay = self.initial_delay
        return

    def next_delay(self) -> float:
        delay = min(self.current_delay, self.max_delay)
        next_delay = self.previous_delay + self.current_delay
        self.previous_delay = self.current_delay
        self.current_delay = max(next_delay, self.initial_delay)
        return delay


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)
    return


def getenv_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    try:
        return int(value, 10)
    except ValueError as exc:
        raise SystemExit(f"invalid integer in {name}: {value!r}") from exc


def getenv_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise SystemExit(f"invalid float in {name}: {value!r}") from exc


def recv_exact(sock: socket.socket, size: int) -> bytes:
    chunks = []
    remaining = size
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise EOFError("peer closed the TCP connection")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def create_can_socket(iface: str) -> socket.socket:
    sock = socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW)

    sol_can_raw = getattr(socket, "SOL_CAN_RAW", 101)
    can_raw_recv_own_msgs = getattr(socket, "CAN_RAW_RECV_OWN_MSGS", 4)
    can_raw_fd_frames = getattr(socket, "CAN_RAW_FD_FRAMES", 5)

    try:
        sock.setsockopt(sol_can_raw, can_raw_recv_own_msgs, 0)
    except OSError:
        pass

    try:
        sock.setsockopt(sol_can_raw, can_raw_fd_frames, 1)
    except OSError:
        pass

    sock.bind((iface,))
    sock.settimeout(1.0)
    return sock


def configure_tcp_socket(sock: socket.socket, idle_timeout: float | None = None) -> None:
    if idle_timeout is None:
        idle_timeout = DEFAULT_TCP_IDLE_TIMEOUT
    if idle_timeout <= 0.0:
        raise ValueError("idle_timeout must be greater than 0")
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.settimeout(idle_timeout)
    return


def build_control_message(control_type: int) -> bytes:
    if control_type not in {CONTROL_PING, CONTROL_PONG}:
        raise ValueError(f"unsupported control message: {control_type}")
    header = CONTROL_FRAME_SIZE.to_bytes(FRAME_HEADER_SIZE, byteorder="big")
    payload = control_type.to_bytes(1, byteorder="big")
    return header + payload


def send_control_over_tcp(tcp_sock: socket.socket, control_type: int, send_lock: threading.Lock) -> None:
    message = build_control_message(control_type)
    with send_lock:
        tcp_sock.sendall(message)
    return


def send_frame_over_tcp(tcp_sock: socket.socket, frame: bytes, send_lock: threading.Lock) -> None:
    frame_len = len(frame)
    if frame_len not in VALID_FRAME_SIZES:
        raise ValueError(f"unsupported CAN frame size: {frame_len}")
    header = frame_len.to_bytes(FRAME_HEADER_SIZE, byteorder="big")
    with send_lock:
        tcp_sock.sendall(header + frame)
    return


def recv_message_from_tcp(tcp_sock: socket.socket):
    header = recv_exact(tcp_sock, FRAME_HEADER_SIZE)
    frame_len = int.from_bytes(header, byteorder="big")

    if frame_len == CONTROL_FRAME_SIZE:
        control_type = recv_exact(tcp_sock, 1)[0]
        if control_type not in {CONTROL_PING, CONTROL_PONG}:
            raise ProtocolError(f"peer sent invalid control message: {control_type}")
        return "control", control_type

    if frame_len not in VALID_FRAME_SIZES:
        raise ProtocolError(f"peer sent invalid CAN frame size: {frame_len}")

    frame = recv_exact(tcp_sock, frame_len)
    return "frame", frame


def close_tcp_socket(tcp_sock: socket.socket) -> None:
    try:
        tcp_sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    try:
        tcp_sock.close()
    except OSError:
        pass
    return


def perform_initial_heartbeat(tcp_sock: socket.socket, handshake_timeout: float):
    send_lock = threading.Lock()
    buffered_messages = []
    deadline = time.monotonic() + handshake_timeout

    send_control_over_tcp(tcp_sock, CONTROL_PING, send_lock)

    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0.0:
                raise HandshakeFailed(
                    f"no PONG received within {handshake_timeout:.1f}s"
                )

            tcp_sock.settimeout(remaining)
            message_type, payload = recv_message_from_tcp(tcp_sock)

            if message_type == "control" and payload == CONTROL_PONG:
                return buffered_messages

            if message_type == "control" and payload == CONTROL_PING:
                send_control_over_tcp(tcp_sock, CONTROL_PONG, send_lock)
                continue

            buffered_messages.append((message_type, payload))
    finally:
        configure_tcp_socket(tcp_sock)


def bridge(
    can_sock: socket.socket,
    tcp_sock: socket.socket,
    peer_label: str,
    heartbeat_enabled: bool,
    heartbeat_interval: float,
    heartbeat_timeout: float,
    prefetched_messages=None,
) -> None:
    stop_event = threading.Event()
    error_lock = threading.Lock()
    send_lock = threading.Lock()
    first_error = {"value": None}
    last_pong_monotonic = {"value": time.monotonic()}

    if prefetched_messages is None:
        prefetched_messages = []

    def stop_with_error(exc: BaseException) -> None:
        with error_lock:
            if first_error["value"] is None:
                first_error["value"] = exc
        stop_event.set()
        close_tcp_socket(tcp_sock)
        return

    def handle_tcp_message(message_type: str, payload) -> None:
        if message_type == "frame":
            can_sock.send(payload)
            return

        control_type = payload
        if control_type == CONTROL_PING:
            send_control_over_tcp(tcp_sock, CONTROL_PONG, send_lock)
            return
        if control_type == CONTROL_PONG:
            last_pong_monotonic["value"] = time.monotonic()
            return
        raise ValueError(f"unexpected control message: {control_type}")

    def can_to_tcp_worker() -> None:
        while not stop_event.is_set():
            try:
                frame = can_sock.recv(CANFD_MTU)
            except socket.timeout:
                continue
            except OSError as exc:
                stop_with_error(exc)
                return

            if not frame:
                continue

            try:
                send_frame_over_tcp(tcp_sock, frame, send_lock)
            except BaseException as exc:
                stop_with_error(exc)
                return
        return

    def tcp_to_can_worker() -> None:
        try:
            for message_type, payload in prefetched_messages:
                if stop_event.is_set():
                    return
                handle_tcp_message(message_type, payload)

            while not stop_event.is_set():
                message_type, payload = recv_message_from_tcp(tcp_sock)
                handle_tcp_message(message_type, payload)
        except BaseException as exc:
            if not stop_event.is_set():
                stop_with_error(exc)
            return
        return

    def heartbeat_worker() -> None:
        if heartbeat_interval <= 0.0 or heartbeat_timeout <= 0.0:
            return

        while not stop_event.wait(heartbeat_interval):
            now = time.monotonic()
            if now - last_pong_monotonic["value"] > heartbeat_timeout:
                stop_with_error(
                    HeartbeatTimeout(
                        f"heartbeat timeout after {heartbeat_timeout:.1f}s without PONG"
                    )
                )
                return

            try:
                send_control_over_tcp(tcp_sock, CONTROL_PING, send_lock)
            except BaseException as exc:
                stop_with_error(exc)
                return
        return

    workers = [
        threading.Thread(target=can_to_tcp_worker, name="can_to_tcp", daemon=True),
        threading.Thread(target=tcp_to_can_worker, name="tcp_to_can", daemon=True),
    ]

    if heartbeat_enabled:
        workers.append(
            threading.Thread(target=heartbeat_worker, name="heartbeat", daemon=True)
        )

    for worker in workers:
        worker.start()

    for worker in workers:
        worker.join()

    close_tcp_socket(tcp_sock)

    exc = first_error["value"]
    if exc is None:
        return
    if isinstance(exc, EOFError):
        log(f"[{peer_label}] disconnected")
        return
    if isinstance(exc, HeartbeatTimeout):
        log(f"[{peer_label}] {exc}")
        return
    if isinstance(exc, ProtocolError):
        log(f"[{peer_label}] protocol error: {exc}")
        return
    if isinstance(exc, (BrokenPipeError, ConnectionResetError, TimeoutError)):
        log(f"[{peer_label}] TCP disconnected: {exc}")
        return
    if isinstance(exc, OSError):
        log(f"[{peer_label}] I/O error: {exc}")
        return
    raise exc


def run_server() -> int:
    iface = os.environ.get("CAN_IFACE", DEFAULT_IFACE)
    listen_host = os.environ.get("CANPROXY_LISTEN_HOST", DEFAULT_SERVER_HOST)
    listen_port = getenv_int("CANPROXY_LISTEN_PORT", DEFAULT_SERVER_PORT)
    tcp_idle_timeout = getenv_float("CANPROXY_TCP_IDLE_TIMEOUT", DEFAULT_TCP_IDLE_TIMEOUT)
    heartbeat_interval = getenv_float("CANPROXY_HEARTBEAT_INTERVAL", DEFAULT_HEARTBEAT_INTERVAL)
    heartbeat_timeout = getenv_float("CANPROXY_HEARTBEAT_TIMEOUT", DEFAULT_HEARTBEAT_TIMEOUT)

    if tcp_idle_timeout <= 0.0:
        raise SystemExit("CANPROXY_TCP_IDLE_TIMEOUT must be greater than 0")
    if heartbeat_interval <= 0.0:
        raise SystemExit("CANPROXY_HEARTBEAT_INTERVAL must be greater than 0")
    if heartbeat_timeout <= heartbeat_interval:
        raise SystemExit("CANPROXY_HEARTBEAT_TIMEOUT must be greater than CANPROXY_HEARTBEAT_INTERVAL")
    if tcp_idle_timeout <= heartbeat_interval:
        raise SystemExit("CANPROXY_TCP_IDLE_TIMEOUT must be greater than CANPROXY_HEARTBEAT_INTERVAL")

    can_sock = create_can_socket(iface)

    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_sock.bind((listen_host, listen_port))
    listen_sock.listen(1)

    log(
        f"[server] listening on {listen_host}:{listen_port}, CAN iface={iface}, "
        f"tcp_idle_timeout={tcp_idle_timeout:.1f}s, "
        f"heartbeat={heartbeat_interval:.1f}s/{heartbeat_timeout:.1f}s"
    )

    while True:
        conn, addr = listen_sock.accept()
        configure_tcp_socket(conn, tcp_idle_timeout)
        peer_label = f"{addr[0]}:{addr[1]}"
        log(f"[server] accepted {peer_label}")
        try:
            bridge(
                can_sock,
                conn,
                peer_label,
                heartbeat_enabled=True,
                heartbeat_interval=heartbeat_interval,
                heartbeat_timeout=heartbeat_timeout,
            )
        except Exception as exc:
            log(f"[server] connection handler failed for {peer_label}: {exc!r}")
            close_tcp_socket(conn)

    return 0


def connect_tcp(host: str, port: int, timeout: float) -> socket.socket:
    conn = socket.create_connection((host, port), timeout=timeout)
    configure_tcp_socket(conn)
    return conn


def run_client() -> int:
    iface = os.environ.get("CAN_IFACE", DEFAULT_IFACE)
    server_host = os.environ.get("CANPROXY_SERVER_HOST")
    server_port = getenv_int("CANPROXY_SERVER_PORT", DEFAULT_SERVER_PORT)
    reconnect_initial_delay = getenv_float("CANPROXY_RECONNECT_DELAY", DEFAULT_RECONNECT_DELAY)
    reconnect_max_delay = getenv_float(
        "CANPROXY_RECONNECT_MAX_DELAY", DEFAULT_RECONNECT_MAX_DELAY
    )
    connect_timeout = getenv_float("CANPROXY_CONNECT_TIMEOUT", DEFAULT_CONNECT_TIMEOUT)
    handshake_timeout = getenv_float("CANPROXY_HANDSHAKE_TIMEOUT", DEFAULT_HANDSHAKE_TIMEOUT)
    heartbeat_interval = getenv_float(
        "CANPROXY_HEARTBEAT_INTERVAL", DEFAULT_HEARTBEAT_INTERVAL
    )
    heartbeat_timeout = getenv_float(
        "CANPROXY_HEARTBEAT_TIMEOUT", DEFAULT_HEARTBEAT_TIMEOUT
    )

    if server_host is None or server_host == "":
        raise SystemExit("CANPROXY_SERVER_HOST is required in client mode")
    if reconnect_initial_delay <= 0.0:
        raise SystemExit("CANPROXY_RECONNECT_DELAY must be greater than 0")
    if reconnect_max_delay < reconnect_initial_delay:
        raise SystemExit(
            "CANPROXY_RECONNECT_MAX_DELAY must be greater than or equal to "
            "CANPROXY_RECONNECT_DELAY"
        )
    if handshake_timeout <= 0.0:
        raise SystemExit("CANPROXY_HANDSHAKE_TIMEOUT must be greater than 0")
    if heartbeat_interval <= 0.0:
        raise SystemExit("CANPROXY_HEARTBEAT_INTERVAL must be greater than 0")
    if heartbeat_timeout <= heartbeat_interval:
        raise SystemExit("CANPROXY_HEARTBEAT_TIMEOUT must be greater than CANPROXY_HEARTBEAT_INTERVAL")

    reconnect_backoff = FibonacciBackoff(reconnect_initial_delay, reconnect_max_delay)

    can_sock = create_can_socket(iface)
    log(
        f"[client] target={server_host}:{server_port}, CAN iface={iface}, "
        f"handshake={handshake_timeout:.1f}s, "
        f"heartbeat={heartbeat_interval:.1f}s/{heartbeat_timeout:.1f}s"
    )

    while True:
        try:
            conn = connect_tcp(server_host, server_port, connect_timeout)
        except OSError as exc:
            delay = reconnect_backoff.next_delay()
            log(f"[client] TCP connect failed: {exc}; retrying in {delay:.1f}s")
            time.sleep(delay)
            continue

        try:
            prefetched_messages = perform_initial_heartbeat(conn, handshake_timeout)
        except BaseException as exc:
            delay = reconnect_backoff.next_delay()
            log(f"[client] heartbeat handshake failed: {exc}; retrying in {delay:.1f}s")
            close_tcp_socket(conn)
            time.sleep(delay)
            continue

        reconnect_backoff.reset()
        log("[client] connected")
        bridge(
            can_sock,
            conn,
            f"{server_host}:{server_port}",
            heartbeat_enabled=True,
            heartbeat_interval=heartbeat_interval,
            heartbeat_timeout=heartbeat_timeout,
            prefetched_messages=prefetched_messages,
        )
        delay = reconnect_backoff.next_delay()
        log(f"[client] reconnecting in {delay:.1f}s")
        time.sleep(delay)

    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in {"server", "client"}:
        print(
            f"usage: {argv[0]} <server|client>",
            file=sys.stderr,
            flush=True,
        )
        return 1

    if argv[1] == "server":
        return run_server()
    return run_client()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
CANPROXY

    docker build -t "$IMAGE" "$BUILD_DIR"
    echo "[*] Build complete."
fi

# ── connect ───────────────────────────────────────────────────────────────────
echo "[*] Connecting to $HOST:$PORT ..."
exec docker run --rm -it \
    --cap-add NET_ADMIN \
    --add-host=host.docker.internal:host-gateway \
    -e CANPROXY_SERVER_HOST="$HOST" \
    -e CANPROXY_SERVER_PORT="$PORT" \
    "$IMAGE"
