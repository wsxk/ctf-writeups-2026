The only distributable file is `dist.zip`.

## Instanced Container

This repo now includes a containerized service for per-instance deployment:

- On container startup, `instance_server.py` generates a random token.
- That token is used as the runtime "flag input" for `generate.py` + `compile.sh`, producing `packed_instance`.
- HTTP serves the packed binary at `GET /binary`.
- A plain TCP service accepts one line (the recovered token). If correct, it returns the real flag.

Build and run:

```bash
docker build -t another-onion .
docker run --rm -p 8000:8000 -p 31337:31337 -e FLAG='dice{real_flag_here}' another-onion
```

Default ports:

- HTTP: `8000`
- Token submit TCP: `31337`

### End-to-End Compose Test

`docker-compose-test.yaml` launches:

- `challenge`: the instance-generating challenge container.
- `solver`: downloads the packed binary from challenge HTTP, runs the solver, executes the solved binary to recover the token, submits it over TCP, and prints the returned flag.

`NSEGMENTS` is shared across both services:

```bash
NSEGMENTS=512 FLAG='dice{real_flag_here}' docker compose -f docker-compose-test.yaml up --build --abort-on-container-exit --exit-code-from solver
```

## Challenge Description
I've peeled an onion before, but this onion would take me years to peel...

## Flag

Flag is: `dice{5p33d_1s_a1s0_imp0rtant_1n_r3ver5e_3ngineer1ng}`

## Solution

This binary contains a big function run() with 512 segments where each segment
performs the following:
 - Read two bytes from stdin
 - Use the two bytes to decrypt the code for the next section (transforming it byte by byte). The decryption algorithm is randomly generated for each segment and is designed to not be reversable.
 - Continue execution. If the input bytes are correct, the next section would contain proper instructions, but
   otherwise it will most likely run into some sort of segfault.
 - The final section, if decrypted, prints out the flag.

The intended solution is to brute-force all 65536 possible inputs for each segment, until the next segment
decrypts to what looks like proper x86 instructions. Speed is important, so the intended solution executes the
binary natively, but uses a lot of trapping and trampolining to control the execution:
 - Start by marking all code and data pages as non-writable. Handle all code and data page writes by first
   backing up the page and then marking the page as writable. Combined with recording the instruction context,
   this allows us to snapshot and restore the whole execution context.
 - For each segment
   - The first pass is to execute until the read() function is called; this is so we can figure out where
     the first read() call is, in order to revert to it for brute-forcing later. To do this, we overwrite the
     read() plt to an illegal instruction, and in the trap handler, write down the read() call address.
   - Subsequent passes will repeatedly revert to the first read() and execute the code while providing a
     different input for the two read() calls (we do this by handling the illegal instruction in read() by
     emulating what read() would've done). Then we keep executing until encountering a write sigsegv, that'll
     tell us where the next code segment is (since decryption starts with the first byte of the next section).
     We single-step that write, so that after that write we can place an illegal instruction at the first byte
     of the next segment. After decryption is complete it will trigger that illegal instruction, allowing us
     to trap again and inspect the decrypted segment. We use the C implementation of capstone to disassemble
     the segment; we require that at least 2 read() calls be in the disassembly, and among those, pick the
     input for which we're able to decrypt the most number of segments.
   - After each attempt, we revert the code and data pages, so that the execution environment is restored
     and placed once again back at the first read() in the current segment.
   - Once we found the correct input, commit that input by executing until the next read(), and continue.
