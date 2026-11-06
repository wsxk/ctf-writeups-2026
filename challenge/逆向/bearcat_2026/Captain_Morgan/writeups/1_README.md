# Captain Morgan

**Category:** Reverse Engineering<br>
**Points:** 499

## Description

A single-line obfuscated Python script (`chall.py`) that reads user input and validates it against a complex bitwise constraint system. The entire program is compressed onto one line with 2,118 semicolon-separated statements.

## Solution

### Step 1: Understand the Obfuscation

The script parses input in the `BCCTF{...}` format and converts the flag content between the braces into a big-endian integer via `int.from_bytes`. It then uses massive nested walrus operator (`:=`) chains to decompose this integer into 232 individual bits by repeated right-shifting, corresponding to 29 bytes of flag content.

### Step 2: Identify the Boolean Circuit

The extracted bits are combined through a large combinational logic circuit using AND, OR, and XOR operations across roughly 2,100 statements. The bitwise expressions `(x | i) & ~(x & i)` are used as an obfuscated form of XOR. Six different variables are all set to the constant `1` through trivially obfuscated expressions like `1 & 1`, `0 | 1`, `1 ^ 0`, etc.

The final variable `bfu` determines the output:
```python
print("in" * bfu + "correct")
```
When `bfu == 0`, the output is `"correct"`.

### Step 3: Solve with Z3

Since the program is a deterministic boolean circuit over the bits of the input integer, it maps directly to a satisfiability problem. The solver:

1. Parses the single-line code into individual statements by splitting on `;`
2. Models the walrus chains by mapping each variable to `LShR(ari, N)` for the appropriate shift count
3. Evaluates all boolean assignments symbolically using Z3's operator overloading
4. Asserts `bfu == 0` and solves
5. Decodes the result: `ari.to_bytes(29, 'big').decode('ascii')`

```bash
$ echo 'BCCTF{Y00_hO_Ho_anD_4_B07Tl3_oF_rUm}' | python3 chall.py
correct
```

The solve runs in under 1 second since the boolean circuit is purely combinational with no loops.

## Flag

`BCCTF{Y00_hO_Ho_anD_4_B07Tl3_oF_rUm}`

## Files

- `solve.py` - Z3-based solver script
