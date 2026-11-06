#!/usr/bin/env python3
import asyncio
import os
import secrets

FLAG = os.environ.get("FLAG", "squ1rrel{FLAG_NOT_SET_IN_ENV}")
ROUNDS = 5
ROUND_TIMEOUT = 5.0
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "1986"))


def F(nonce: bytes) -> bytes:
    raise NotImplementedError


async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        writer.write(f"squ1rrel-o-tron challenge -- {ROUNDS} rounds, {int(ROUND_TIMEOUT)}s each\n".encode())
        await writer.drain()

        for i in range(1, ROUNDS + 1):
            nonce = secrets.token_bytes(32)
            want = F(nonce)

            writer.write(f"round {i}: {nonce.hex()}\n".encode())
            await writer.drain()

            try:
                line = await asyncio.wait_for(reader.readline(), timeout=ROUND_TIMEOUT)
            except asyncio.TimeoutError:
                writer.write(b"nope (timeout)\n")
                await writer.drain()
                return

            got = line.decode("ascii", errors="ignore").strip()
            if len(got) != 32 or not all(c in "0123456789abcdefABCDEF" for c in got):
                writer.write(b"nope (bad format)\n")
                await writer.drain()
                return
            if bytes.fromhex(got) != want:
                writer.write(b"nope (wrong)\n")
                await writer.drain()
                return

        writer.write(f"{FLAG}\n".encode())
        await writer.drain()
    except (ConnectionResetError, BrokenPipeError):
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def main():
    srv = await asyncio.start_server(handle, HOST, PORT)
    addr = ", ".join(str(s.getsockname()) for s in srv.sockets)
    print(f"squ1rrel-o-tron server listening on {addr}", flush=True)
    async with srv:
        await srv.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
