# CTF Challenge Analysis: ooo (LACTF 2025)

**Challenge Category:** Reverse Engineering
**Challenge Name:** ooo (displayed as "000" in directory)
**Flag Format:** `lactf{...}`
**Analysis Date:** 2026-02-06
**Status:** SOLUTION FOUND - Verification Issue Pending

---

## Challenge Description

> Surely everyone knows the difference between the Cyrillic small letter o, the Greek small letter omicron, and the Latin small letter o, right? :)

---

## Known Facts and Verified Behaviors

### 1. Challenge Structure
- Single Python file: `ooo.py`
- Uses Unicode homoglyphs (characters that look like "o") as function names
- Each function performs a different arithmetic operation

### 2. Function Definitions (by Unicode codepoint)

| Function | Codepoint | Unicode Name | Operation |
|----------|-----------|--------------|-----------|
| `о` | U+043E | CYRILLIC SMALL LETTER O | `a + b` |
| `ο` | U+03BF | GREEK SMALL LETTER OMICRON | `a - b` |
| `օ` | U+0585 | ARMENIAN SMALL LETTER OH | `a * b` |
| `ỏ` | U+1ECF | LATIN SMALL LETTER O WITH HOOK ABOVE | `a // b` |
| `ơ` | U+01A1 | LATIN SMALL LETTER O WITH HORN | `a ^ b` (XOR) |
| `ó` | U+00F3 | LATIN SMALL LETTER O WITH ACUTE | `a \| b` (OR) |
| `ὀ` | U+1F40 | GREEK SMALL LETTER OMICRON WITH PSILI | `a & b` (AND) |
| `ὸ` | U+1F78 | GREEK SMALL LETTER OMICRON WITH VARIA | `b - a` |
| `ὄ` | U+1F44 | GREEK SMALL LETTER OMICRON WITH PSILI AND OXIA | `a` (returns first) |
| `ὂ` | U+1F42 | GREEK SMALL LETTER OMICRON WITH PSILI AND VARIA | `b` (returns second) |
| `ȯ` | U+022F | LATIN SMALL LETTER O WITH DOT ABOVE | `a % b` |

### 3. Target Array
```python
ὁ = [205, 196, 215, 218, 225, 226, 1189, 2045, 2372, 9300, 8304, 660, 8243,
     16057, 16113, 16057, 16004, 16007, 16006, 8561, 805, 346, 195, 201,
     154, 146, 223]
```
- Length: 27 elements

### 4. Validation Logic (Line 36)
```python
if (о(ὄ(ό,ὃ),ὂ(ό,ὃ)) != ὁ[ơ(ö,ȯ(օ(ό,ὃ),ό))]):
```

**Decoded:**
- `ό` = `ord(guess[i])` (current character)
- `ὃ` = `ord(guess[i+1])` (next character)
- `ö` = loop index

**Left side (value check):**
- `ὄ(ό,ὃ)` = `ό` (returns first arg)
- `ὂ(ό,ὃ)` = `ὃ` (returns second arg)
- `о(ό, ὃ)` = `ό + ὃ` (addition)
- **Result: `guess[i] + guess[i+1]`**

**Right side (index calculation):**
- `օ(ό,ὃ)` = `ό * ὃ`
- `ȯ(ό*ὃ, ό)` = `(ό * ὃ) % ό` = `0` (always, when ό ≠ 0)
- `ơ(ö, 0)` = `ö ^ 0` = `ö`
- **Result: `ὁ[i]`**

**Simplified constraint:**
```
guess[i] + guess[i+1] == ὁ[i]  for i in range(26)
```

### 5. Loop Bounds
- Loop: `range(len(ὁ)-1)` = `range(26)` = indices 0-25
- Checks 26 pairs of adjacent characters
- Requires minimum 27 characters (indices 0-26)
- Element `ὁ[26] = 223` encodes the final pair for proper flag format

---

## Derived Solution

### Algorithm
Starting with known first character 'l' (108), solve forward:
```python
flag[0] = 108  # 'l'
flag[i+1] = ὁ[i] - flag[i]  for i in range(27)
```

### Computed Flag (28 characters)
```
lactf{gоοօỏơóὀόὸὁὃὄὂȯöd_j0b}
```

### Character Breakdown
| Index | Char | Codepoint | Unicode Name |
|-------|------|-----------|--------------|
| 0 | l | U+006C | LATIN SMALL LETTER L |
| 1 | a | U+0061 | LATIN SMALL LETTER A |
| 2 | c | U+0063 | LATIN SMALL LETTER C |
| 3 | t | U+0074 | LATIN SMALL LETTER T |
| 4 | f | U+0066 | LATIN SMALL LETTER F |
| 5 | { | U+007B | LEFT CURLY BRACKET |
| 6 | g | U+0067 | LATIN SMALL LETTER G |
| 7 | о | U+043E | CYRILLIC SMALL LETTER O |
| 8 | ο | U+03BF | GREEK SMALL LETTER OMICRON |
| 9 | օ | U+0585 | ARMENIAN SMALL LETTER OH |
| 10 | ỏ | U+1ECF | LATIN SMALL LETTER O WITH HOOK ABOVE |
| 11 | ơ | U+01A1 | LATIN SMALL LETTER O WITH HORN |
| 12 | ó | U+00F3 | LATIN SMALL LETTER O WITH ACUTE |
| 13 | ὀ | U+1F40 | GREEK SMALL LETTER OMICRON WITH PSILI |
| 14 | ό | U+1F79 | GREEK SMALL LETTER OMICRON WITH OXIA |
| 15 | ὸ | U+1F78 | GREEK SMALL LETTER OMICRON WITH VARIA |
| 16 | ὁ | U+1F41 | GREEK SMALL LETTER OMICRON WITH DASIA |
| 17 | ὃ | U+1F43 | GREEK SMALL LETTER OMICRON WITH DASIA AND VARIA |
| 18 | ὄ | U+1F44 | GREEK SMALL LETTER OMICRON WITH PSILI AND OXIA |
| 19 | ὂ | U+1F42 | GREEK SMALL LETTER OMICRON WITH PSILI AND VARIA |
| 20 | ȯ | U+022F | LATIN SMALL LETTER O WITH DOT ABOVE |
| 21 | ö | U+00F6 | LATIN SMALL LETTER O WITH DIAERESIS |
| 22 | d | U+0064 | LATIN SMALL LETTER D |
| 23 | _ | U+005F | LOW LINE |
| 24 | j | U+006A | LATIN SMALL LETTER J |
| 25 | 0 | U+0030 | DIGIT ZERO |
| 26 | b | U+0062 | LATIN SMALL LETTER B |
| 27 | } | U+007D | RIGHT CURLY BRACKET |

### Visual Interpretation
The middle section uses 15 different "o" homoglyphs to spell "good" visually:
`g` + `оοօỏơóὀόὸὁὃὄὂȯö` + `d` = "good" (visually)

Full flag reads as: **lactf{good_j0b}** (visually)

---

## Verification Results

### Local Script Verification: PASSED
```bash
$ python3 -c "..." | python3 ooo.py
What's the flag? That's the flag! :)
```

### UTF-8 Hex Representation
```
6c616374667b67d0bececbfd685e1bb8fc6a1c3b3e1bd80e1bdb9e1bdb8e1bd81e1bd83e1bd84e1bd82c8afc3b6645f6a30627d
```

### Python Codepoints (for exact reproduction)
```python
[108,97,99,116,102,123,103,1086,959,1413,7887,417,243,8000,8057,8056,8001,8003,8004,8002,559,246,100,95,106,48,98,125]
```

---

## Techniques Attempted

### 1. Direct Analysis of Obfuscated Code
- **Status:** Successful
- Identified all homoglyph function names and their operations
- Decoded the validation logic

### 2. Constraint Solving
- **Status:** Successful
- Simplified validation to: `guess[i] + guess[i+1] == target[i]`
- Solved forward from known prefix "lactf{"

### 3. Echo/Pipe Testing
- **Status:** Partial success
- Direct echo failed (Unicode encoding issues in shell)
- Python subprocess piping works correctly

---

## Invalid Hypotheses and Misdirections

### 1. "The index might not always be i"
- **Status:** Disproven
- `(a * b) % a` is always 0 when a ≠ 0
- Index simplifies to `i ^ 0 = i`

### 2. "27-character flag might work"
- **Status:** Disproven
- 27-char version missing closing `}`
- Only 28-char version is a valid flag format

### 3. "Simplified ASCII flag might be accepted"
- **Status:** Unknown
- `lactf{goooooooooooooood_j0b}` would NOT pass local validation
- The Unicode characters are mathematically required

---

## Remaining Uncertainties

1. **CTF Platform Submission**
   - User reports flag is "incorrect" when submitted
   - Possible causes:
     - Unicode normalization by web form
     - Copy-paste encoding issues
     - CTF has ended / flags expired
     - Platform-specific encoding requirements

2. **Submission Method Unknown**
   - Web form vs API vs other?
   - What error message is displayed?

3. **CTF Status Unknown**
   - Is this a live or archived challenge?

---

## Prioritized Next Steps

### Priority 1: Verify Submission Method
- [ ] Determine how user is submitting (web form, API, etc.)
- [ ] Check what error message CTF platform returns
- [ ] Verify if CTF is still active

### Priority 2: Alternative Submission Formats
- [ ] Try submitting via file upload if available
- [ ] Try URL-encoded version: `lactf%7Bg%D0%BE%CE%BF%D6%85...`
- [ ] Try base64 encoded if platform supports it

### Priority 3: Direct Copy Methods
- [ ] Use Python to generate and copy directly to clipboard:
  ```bash
  python3 -c "print(''.join(chr(c) for c in [108,97,99,116,102,123,103,1086,959,1413,7887,417,243,8000,8057,8056,8001,8003,8004,8002,559,246,100,95,106,48,98,125]))" | xclip -selection clipboard
  ```
- [ ] Read from saved file: `/tmp/flag.txt`

### Priority 4: Alternative Interpretations
- [ ] Check if challenge has multiple valid solutions
- [ ] Review challenge hints/discussion for additional context
- [ ] Contact CTF organizers if issue persists

---

## Quick Reference Commands

### Generate Flag
```bash
python3 -c "print(''.join(chr(c) for c in [108,97,99,116,102,123,103,1086,959,1413,7887,417,243,8000,8057,8056,8001,8003,8004,8002,559,246,100,95,106,48,98,125]))"
```

### Verify Flag Locally
```bash
python3 -c "..." | python3 ooo.py
```

### Copy to Clipboard (Linux)
```bash
python3 -c "print(''.join(chr(c) for c in [108,97,99,116,102,123,103,1086,959,1413,7887,417,243,8000,8057,8056,8001,8003,8004,8002,559,246,100,95,106,48,98,125]))" | xclip -selection clipboard
```

---

## Files

| File | Description |
|------|-------------|
| `ooo.py` | Original challenge file |
| `/tmp/flag.txt` | Generated flag (UTF-8 encoded) |
| `analysis.md` | This analysis document |
