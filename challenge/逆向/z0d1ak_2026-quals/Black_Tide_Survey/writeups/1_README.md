# Black Tide Survey

**Category:** Reversing | **Points:** 500 | **Author:** pokymono | **Flag:** `zdk{sa81_Sa_7ELO}`

## Description
> Survey unit BT-04 was recovered twelve nautical miles east of its assigned transect. Recover the final surveyed image and identify the marked vessel.

## TL;DR
We get a recording from a wrecked underwater survey drone and a stripped "diagnostic" tool that opens it but produces a scrambled image. Reverse the tool to learn the container format, decode the sonar pings, undo the deliberate scrambling (interleaved records + one channel stored backwards), and a text label painted into the water pops out at the edge of the survey. The catch: it's drawn in a chunky, intentionally ambiguous pixel font, and both the "obvious" reading and a painted hull number are decoys. The honest glyph-by-glyph read is `sa81_Sa_7ELO`.

## Initial Analysis

The handout `rev_black-tide-survey.zip` contains:

| File | What it is |
|---|---|
| `sonar_diag` | 18 KB stripped x86-64 ELF — a field diagnostic converter |
| `dock_calibration.bts` / `dock_reference.png` | A known calibration survey + expected output |
| `final_transect.bts` | The mission survey we care about |
| `RECOVERY_NOTE.txt` | "Flavor text" that is actually a spec |

`file` shows a stripped PIE; `strings` is nearly empty (just a usage string and error messages) — no flag baked in, so the answer lives inside the *decoded image*. Running the tool produces obviously wrong output: the scene looks duplicated and mirrored, like a double-exposure.

**The recovery note is a cheat sheet.** Every line maps to a decoding step:
- *"refuses this head revision" / "sample ordering never documented"* → samples decode in a weird order on purpose.
- *"Near water is not near ground"* → side-scan sonar; first samples are the water column, not the ground beneath.
- *"Port comes home; starboard goes away"* → the two channels are stored in opposite directions; one is reversed.
- *"navigation clock 3.8 s ahead"* → red herring for the flag.

## Vulnerability / Core Concept

Reversing `sonar_diag` hands us the whole **BTS2** container for free:

- **32-byte header** (`<4sHHIHHIIII`): magic `BTS2`, version 2, `side_bins=384`, `ping_count`, CRC32 over the first 28 bytes.
- **Records** `[4-byte type][u32 size][u32 crc32][payload]`: `META`, `CALB` (gain table), `PING × N` (1176 bytes each), `DONE`. Every CRC validates.
- **Each PING**: 24-byte telemetry + two 576-byte channels (port, starboard).
- **Each channel** = 384 twelve-bit samples, packed 3 bytes → 2 words, then **zig-zag delta encoded**:

```python
a = byte0 | ((byte1 & 0x0f) << 8)
b = (byte1 >> 4) | (byte2 << 4)
delta  = (word >> 1) ^ -(word & 1)     # un-zigzag
sample = (previous + delta) & 0xfff
```

The scrambling is two deliberate tricks:
1. **Records stored even-then-odd** — pings appear as `0,2,4,…,1,3,5,…`, so the survey looks like it plays twice. **Fix:** sort pings by their `sequence` field.
2. **Port channel stored backwards** (the "Port comes home" clue). **Fix:** reverse it consistently.

Once sorted, a coherent scene emerges with a boat whose hull number reads `SABLE-7319`. That's a **decoy** — "identify the marked vessel" means find what was *marked onto* the survey.

## Exploitation

The real payload is a clean digital bitmap hidden in the noise at the top/bottom edges of the sorted starboard channel. Sample values there are pinned to sentinels:
- `3840 (0xF00)` = "on" pixel, `256 (0x100)` = "off" pixel, everything else = ordinary speckle.

And the text rows sit on **every other ping** (odd pings between them are speckle — that's the banding that tempts you to give up). Extraction (`solve.py`, `work/marker3.py`, `work/ascii_marker.py`):

1. Parse BTS2, validate CRCs, decode each channel (12-bit unpack + zig-zag delta).
2. Sort pings by `sequence` to kill the double-exposure.
3. Stack the starboard channel into a `pings × 384` image.
4. Keep only rows whose values are exactly `0xF00`/`0x100`, binarize (`0xF00 → white`), and read the glyphs.

The blocky 3-pixel font was chosen because several glyphs are near-identical. Reading carefully:

```
s a 8 1 _ S a _ 7 E L O   ->   sa81_Sa_7ELO
```

The "friendly" misreading `sable_5a_7E10` teases the painted hull name **SABLE** and looks like tidy hex — that's the trap. Real disambiguations: `8` vs `b`, `1` vs `l`, `S` vs `5`, `L` vs `1`, `O` vs `0`.

The dock calibration pair is the sanity check: reproducing its geometry byte-for-byte confirms the decode before trusting the final transect.

> Excluded from this directory: the `.bts` recordings, `sonar_diag` binary, and reference/recovered PNGs. `solve.py` is included; helper `work/*.py` scripts are referenced.

## Flag
`zdk{sa81_Sa_7ELO}`

## Key Takeaways
- **The flavor text was the spec** — every line of the recovery note mapped to a concrete decoding step.
- **Reverse the reader, don't fight the writer** — the stripped tool handed us the entire container + compression format.
- **"Wrong-looking" output is usually scrambled, not broken** — a sort by sequence fixed the double-exposure.
- **Hidden-in-noise bitmaps** pinned to exact sentinel values stand out instantly from real sensor speckle.
- **Beware decoy strings and cruel fonts** — the answer needed pixel-level glyph disambiguation.
