# Brick by Brick

**Category:** Hardware | **Difficulty:** Easy | **Flag:** `UMASS{U4R7_15_7h3_b357,_r1gh7?}`

## TL;DR

We're given a logic analyzer CSV capture of a serial signal. The trick is recognizing it as UART at 33,333 baud, decoding the binary waveform into bytes, and finding a hex-encoded flag buried in fake Linux boot logs.

## What We're Given

The challenge hands us a single file: `code.csv` — a 1.2 MB logic analyzer capture. The CSV has two columns, `timestamp` and `logic_level`, with about 56,990 samples spanning roughly 1.7 seconds. The logic levels are just 0 and 1 — a binary waveform.

The challenge title "Brick by Brick" and its flavor text reference a LEGO controller, which is thematic dressing. What we actually have is a raw serial communication capture from some embedded system.

```
timestamp,logic_level
0.0,1
2.9960751415645503e-05,1
5.992150283129101e-05,1
...
0.00014980375707822753,0
0.00017976450849387305,1
```

The timestamps are floating-point seconds, and the samples are spaced about 30 microseconds apart. Already this is telling us something — 30us is a very specific number.

## Initial Recon

First thing we want to understand: what kind of signal is this? Logic analyzer captures usually mean we're dealing with some kind of serial protocol — UART, SPI, I2C, and friends. The key to telling them apart is timing.

Let's figure out the "pulse widths" — how long each run of 0s or 1s lasts. We group consecutive identical samples together and measure how long each group takes.

When we do this analysis on `code.csv`, the pulse width distribution jumps out immediately:

- ~30us — appears 8,271 times
- ~60us — appears 5,935 times
- ~90us — appears 1,264 times
- ~180us — appears 4,618 times

Everything is a multiple of 30us. This is the dead giveaway: we have a **bit-time** of 30 microseconds. Whatever protocol this is, each bit takes 30us to transmit — which works out to 1/0.000030 ≈ **33,333 baud**.

## The Vulnerability / Trick

This is a UART decode challenge. UART (Universal Asynchronous Receiver-Transmitter) is one of the oldest and simplest serial protocols around — it's how microcontrollers and embedded systems have been chatting with each other since basically forever. It's also one of the first things to look for when you see a single-channel binary waveform in a CTF.

Here's how UART framing works:
- The line idles **HIGH** (1) when nothing is being transmitted
- Each character starts with a **start bit** — a single LOW (0) that says "incoming byte"
- Then 8 **data bits**, transmitted **LSB first** (least significant bit comes out first)
- Then a **stop bit** — a HIGH (1) to return to idle

So a byte arriving looks like: `[0][b0][b1][b2][b3][b4][b5][b6][b7][1]` — that's 10 bit-times total for each character.

At 33,333 baud with an 8N1 frame (8 data bits, no parity, 1 stop bit), the sample spacing of ~30us fits perfectly. That's our protocol.

The way to decode it is "center sampling" — when you see a falling edge (the start bit), you wait 1.5 bit-times to land in the middle of the first data bit, sample, then wait 1 full bit-time for each subsequent bit. This way you avoid reading on the edges where the signal might be transitioning.

## Building the Exploit

Here's the decode logic in Python, step by step.

**Step 1: Load the CSV and group consecutive samples into pulses.**

```python
import csv

timestamps = []
levels = []
with open('code.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        timestamps.append(float(row['timestamp']))
        levels.append(int(row['logic_level']))

# Group into runs: (level, duration)
pulses = []
i = 0
while i < len(levels):
    j = i
    while j < len(levels) and levels[j] == levels[i]:
        j += 1
    duration = timestamps[j-1] - timestamps[i] if j < len(timestamps) else 0
    pulses.append((levels[i], duration))
    i = j
```

Now we have a list of (level, duration) pairs — each entry is "the signal was HIGH/LOW for this many seconds."

**Step 2: Convert pulses to individual bits.**

Since each bit takes 30us (0.00003 seconds), we can figure out how many bits each pulse represents by dividing its duration by the bit time.

```python
BIT_TIME = 30e-6  # 30 microseconds

bits = []
for level, duration in pulses:
    count = round(duration / BIT_TIME)
    bits.extend([level] * count)
```

**Step 3: Find start bits and decode bytes.**

We scan through the bit stream looking for a HIGH→LOW transition. When we find one (that's our start bit), we jump 1.5 bit-times ahead to sample the first data bit, then grab 8 bits total, LSB first.

```python
decoded = []
i = 0
while i < len(bits) - 10:
    # Look for falling edge (start bit: HIGH to LOW)
    if i > 0 and bits[i-1] == 1 and bits[i] == 0:
        # We're at the start bit. Jump to center of first data bit.
        data_start = i + 1  # skip the start bit itself
        byte_val = 0
        for bit_pos in range(8):
            sample_idx = data_start + bit_pos
            if sample_idx < len(bits):
                byte_val |= (bits[sample_idx] << bit_pos)  # LSB first
        # Verify stop bit is HIGH
        stop_idx = data_start + 8
        if stop_idx < len(bits) and bits[stop_idx] == 1:
            decoded.append(byte_val)
        i = stop_idx + 1
    else:
        i += 1

print(bytes(decoded).decode('ascii', errors='replace'))
```

**Step 4: Find the flag in the decoded output.**

When we run this, we get 3,799 bytes of Linux kernel boot messages — the fake "LEGO controller" booting up. Scrolling through it, one line sticks out:

```
[    0.037500] secretflag: 554d4153537b553452375f31355f3768335f623335372c5f72316768373f7d
```

That hex string doesn't look like a memory address or a kernel identifier. Let's decode it:

```bash
echo "554d4153537b553452375f31355f3768335f623335372c5f72316768373f7d" | xxd -r -p
```

Output: `UMASS{U4R7_15_7h3_b357,_r1gh7?}`

There it is. The flag is a loving tribute to the protocol we just decoded.

## Running It

```
$ python3 solve.py
...
[    0.036000] Arch Linux
[    0.036500] LEGO Mindstorms EV3 Controller
[    0.037000] Initializing GPIO subsystem...
[    0.037500] secretflag: 554d4153537b553452375f31355f3768335f623335372c5f72316768373f7d
[    0.038000] GPIO initialized.
...

$ echo "554d4153537b553452375f31355f3768335f623335372c5f72316768373f7d" | xxd -r -p
UMASS{U4R7_15_7h3_b357,_r1gh7?}
```

Flag: `UMASS{U4R7_15_7h3_b357,_r1gh7?}` — "UART is the best, right?" in leetspeak. The challenge author had a sense of humor.

## Key Takeaways

- **Pulse width analysis is the first step for any unknown serial protocol.** If all durations are multiples of some base unit, that base unit is your bit time. Work out the baud rate (1 / bit_time) and you're halfway there.
- **UART is everywhere in hardware CTFs.** When you see a single-channel binary waveform from a logic analyzer, start with UART. It's 8N1 by default (8 data bits, no parity, 1 stop bit). Check for idle-HIGH with a falling start bit.
- **LSB first is easy to forget.** UART sends the least significant bit first, so when you reconstruct the byte, you OR in each bit shifted left by its position index — `byte_val |= (bit << bit_pos)`.
- **The flag can be anywhere in the decoded data.** Here it was hidden in a "kernel log" styled as a `secretflag:` line with hex-encoded content. When decoding embedded data, always scan the full output rather than just looking at the first few bytes.
- **Tools for hardware CTFs:** Logic2 (Saleae's software), PulseView/sigrok, and even a basic Python script like this one all work. If you're doing this repeatedly, sigrok's built-in UART decoder is a huge time saver.
