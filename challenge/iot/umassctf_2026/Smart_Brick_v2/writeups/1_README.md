# Smart Brick v2

**Category:** Hardware | **Difficulty:** Medium | **Points:** 500 | **Flag:** `UMASS{In_Th3_G4t3s}`

## TL;DR

We're given a KiCad PCB design file containing 26 74LS-series logic gate ICs. Each of the 19 onboard LEDs lights up for exactly one 7-bit ASCII input. We parse the netlist, simulate all 128 possible inputs, and read the LEDs in order — they spell the flag. The pun writes itself: the flag is literally *in the gates*.

## What We're Given

A single zip archive: `smart-brick-v2.zip`. Inside is `smart-brick-v2.kicad_pcb` — a KiCad v9 PCB design file for a 4-layer board. The challenge title says "Smart Brick v2" and the category is hardware. No server, no binary, no URL. Just a PCB.

The challenge description hints that we need to figure out what the board *does* — which means we're reverse engineering a hardware circuit purely from its schematic/netlist data.

## Initial Recon

First instinct: search for the flag string directly in the file.

```bash
grep -i "UMASS" extracted/smart-brick-v2.kicad_pcb
# (no output)
```

No luck — the flag isn't sitting in plaintext. So we need to actually understand the circuit.

Opening the `.kicad_pcb` in a text editor (it's a structured text format), we can read out the component list. Running some regex against the `property "Value"` fields gives us a clear picture:

```
26 ICs (all 74LS-series logic gates)
19 LEDs (D1-D19)
19 MOSFETs (Q1-Q19, 2N7002 N-channel)
19 resistors (1K, for LED current limiting)
J1: 8-pin input header (7 signal pins IN0-IN6 + GND)
J2: 2-pin power header (+5V, GND)
```

The IC types break down as:
- **74LS04** (x2) — Hex inverter (NOT gates)
- **74LS21** (x12) — Dual 4-input AND gate
- **74LS27** (x2) — Triple 3-input NOR gate
- **74LS08** (x1) — Quad 2-input AND
- **74LS32** (x1) — Quad 2-input OR
- **74LS86** (x1) — Quad 2-input XOR
- **74LS00** (x1) — Quad 2-input NAND
- **74LS02** (x2) — Quad 2-input NOR
- **74LS20** (x1) — Dual 4-input NAND

All of these are *combinational* logic — no flip-flops, no clock, no memory. This board is a purely stateless logic function: you put 7 bits in, and some subset of LEDs light up. With 7 input pins and 19 LED outputs, and the input range of ASCII printable characters neatly fitting in 7 bits (values 0-127), this is looking very much like a character-display machine.

## The Vulnerability / Trick

There is no vulnerability here in the traditional sense. The trick is understanding what the circuit *computes*. Each LED is driven by a logic expression over the 7 input bits. The challenge is:

> For each LED D1-D19, what 7-bit input value (i.e., which ASCII character) causes it to light up?

Read those characters in order (D1 through D19) and you have the flag.

This is a classic *hardware reversing* challenge. The gate network is the lock; we need to enumerate all 128 combinations and see which key fits each tumbler.

## Building the Exploit

### Step 1: Parse the KiCad netlist

KiCad v9's `.kicad_pcb` format stores everything as nested S-expressions (think Lisp-style parentheses). Each component has a `(footprint ...)` block, and within it, `(pad ...)` blocks that say which net (wire) each pin connects to.

The tricky part: KiCad v9 puts the `(net ...)` tag on its own line *inside* the `(pad ...)` block. A naive single-line regex misses it entirely. We need a proper parenthesis-matching parser.

```python
def find_matching_paren(text, start):
    """Find matching close paren for open paren at start."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return i
    return len(text)
```

With this, we can extract each footprint block, then each pad block within it, and map `pad_number -> net_name` for every component. The full parser is in `parse_pcb2.py`.

### Step 2: Map gates to their logic functions

Each 74LS IC has a well-defined pinout. For example, the 74LS21 (dual 4-input AND) uses pins 1, 2, 4, 5 as inputs and pin 6 as the output for gate 1. We encode these pinout tables:

```python
gate_defs = {
    '74LS21': [
        ([1,2,4,5], 6, 'AND4'), ([9,10,12,13], 8, 'AND4'),
    ],
    '74LS04': [
        ([1], 2, 'NOT'), ([3], 4, 'NOT'), ([5], 6, 'NOT'),
        ([9], 8, 'NOT'), ([11], 10, 'NOT'), ([13], 12, 'NOT'),
    ],
    # ... etc
}
```

By combining the netlist (which net is on each pin) with the pinout (which pins are inputs/outputs), we can build a map of `output_net -> (gate_type, [input_nets])` for every gate on the board.

### Step 3: Trace the LED logic back to inputs

Each LED's brightness is controlled by a MOSFET (Q1-Q19). The MOSFET gate pin connects to some logic net. We trace that net back through the gate graph until we reach the raw input pins IN0-IN6. This gives us the boolean expression that controls each LED.

For example, LED D1 is driven by net G59, which traces back to:

```
G59 = NAND(G57, G58)
G57 = NAND(G7, IN0)
G58 = NAND(G7, NOT(IN0))
G7  = AND4(NOT(IN5), IN4, IN2, G6)
G6  = AND4(IN6, IN0, NOT(IN3), NOT(IN1))
```

This NAND-NAND-of-complements pattern is actually a classic XOR implementation in NAND gates. When G7 is high and exactly one of IN0 or NOT(IN0) is high (which is... always, by definition), G59 goes high. But G7 only goes high for specific input combinations.

### Step 4: Simulate all 128 inputs

Rather than manually simplifying 19 boolean expressions, we just simulate. The `simulate()` function in `solve.py` takes 7 bits and evaluates every gate in topological order, returning which LEDs are active:

```python
def simulate(IN):
    IN0, IN1, IN2, IN3, IN4, IN5, IN6 = IN

    # NOT gates (U1)
    G0 = 1 - IN0  # NOT(IN0)
    G1 = 1 - IN1  # NOT(IN1)
    # ... all 60-something intermediate nets ...

    # LED outputs
    leds = {
        1: G59, 2: G62, 3: G13, 4: G19, 5: G21,
        6: G24, 7: G26, 8: G29, 9: G31, 10: G36,
        11: G39, 12: G41, 13: G43, 14: G45, 15: G47,
        16: G49, 17: G52, 18: G54, 19: G56,
    }
    return leds
```

We loop over all 128 values, track which inputs light each LED, and print the results:

```python
for val in range(128):
    bits = [(val >> i) & 1 for i in range(7)]  # IN0=LSB, IN6=MSB
    leds = simulate(bits)
    active = [i for i in range(1, 20) if leds[i]]
    if active:
        char = chr(val) if 32 <= val < 127 else f'\\x{val:02x}'
        print(f"Input {val:3d} (0b{val:07b}) = '{char}': LEDs {active}")
```

One bit of care: the input connector J1 has IN0 on the LSB. So for the character `U` (ASCII 85 = `0b1010101`), we pass bits `[1,0,1,0,1,0,1]` for IN0 through IN6.

## Running It

```
$ python3 solve.py

=== Testing all 128 input combinations ===

Input  65 (0b1000001) = 'A': LEDs [3]
Input  51 (0b0110011) = '3': LEDs [12, 17]
Input  71 (0b1000111) = 'G': LEDs [14]
Input  73 (0b1001001) = 'I': LEDs [7]
Input  77 (0b1001101) = 'M': LEDs [2]
Input  83 (0b1010011) = 'S': LEDs [4, 5]
Input  84 (0b1010100) = 'T': LEDs [10]
Input  85 (0b1010101) = 'U': LEDs [1]
Input  95 (0b1011111) = '_': LEDs [9, 13]
Input 104 (0b1101000) = 'h': LEDs [11]
Input 110 (0b1101110) = 'n': LEDs [8]
Input 115 (0b1110011) = 's': LEDs [18]
Input 116 (0b1110100) = 't': LEDs [16]
Input  52 (0b0110100) = '4': LEDs [15]
Input 123 (0b1111011) = '{': LEDs [6]
Input 125 (0b1111101) = '}': LEDs [19]

=== LED to character mapping ===
LED D 1: [85]  = 'U'
LED D 2: [77]  = 'M'
LED D 3: [65]  = 'A'
LED D 4: [83]  = 'S'
LED D 5: [83]  = 'S'
LED D 6: [123] = '{'
LED D 7: [73]  = 'I'
LED D 8: [110] = 'n'
LED D 9: [95]  = '_'
LED D10: [84]  = 'T'
LED D11: [104] = 'h'
LED D12: [51]  = '3'
LED D13: [95]  = '_'
LED D14: [71]  = 'G'
LED D15: [52]  = '4'
LED D16: [116] = 't'
LED D17: [51]  = '3'
LED D18: [115] = 's'
LED D19: [125] = '}'

=== Flag (characters that light LEDs D1-D19 in order) ===
UMASS{In_Th3_G4t3s}
```

Every LED lights for exactly one input value. Reading D1 through D19 in sequence: `UMASS{In_Th3_G4t3s}`.

## Key Takeaways

**The core technique:** Hardware reverse engineering by netlist simulation. When you can't run the hardware, you simulate it. This is literally how chip verification works in industry — before a chip is fabricated, you simulate the RTL against test vectors.

**The KiCad parsing gotcha:** KiCad v9 changed the `.kicad_pcb` format to use multi-line pad blocks. If you're writing a parser for KiCad files, don't assume `(net ...)` is on the same line as `(pad ...)`. Use a proper S-expression / parenthesis-depth parser instead.

**The design insight:** A pure combinational circuit with 7 inputs and 19 outputs, where each output fires for exactly one input, is essentially a ROM (read-only memory). The challenge authors encoded each character of the flag as a unique 7-bit minterm, then wired up the corresponding LED to light when that minterm is asserted. It's a hardware lookup table spelled out in discrete logic gates.

**Tools worth knowing:**
- KiCad — free, open-source PCB design tool. The file format is human-readable text.
- 74LS datasheet collection — any pinout question about classic logic ICs is one Google search away. Diodes Inc. and TI have free datasheets.
- Python for simulation — when the logic is complex, don't solve it analytically. Just enumerate.

The flag name says it all: the answer really was *in the gates* the whole time.
