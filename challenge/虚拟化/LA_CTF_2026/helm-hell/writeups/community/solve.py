#!/usr/bin/env python3
"""
Brute force the flag character by character.
For each position, try all printable characters and see which produces 'true'.
"""

import subprocess
import string
import sys

HELM = "/home/kali/.local/bin/helm"
CHARTDIR = "/home/kali/Downloads/lactf2025/rev/helm-hell"
FLAG_LEN = 41

def test_flag(flag):
    """Test if a flag candidate produces 'true'."""
    result = subprocess.run(
        [HELM, "template", ".", "--set", f"input={flag}"],
        cwd=CHARTDIR,
        capture_output=True,
        text=True,
        timeout=30
    )
    return "true" in result.stdout

# The flag starts with lactf{
# Let's verify
known = "lactf{"
remaining = FLAG_LEN - len(known) - 1  # -1 for closing }

# Build the flag incrementally
charset = string.printable[:-5]  # Remove whitespace chars at end

print(f"Starting brute force...")
print(f"Flag length: {FLAG_LEN}")
print(f"Known prefix: {known}")

# First, let's check if the flag format is correct
# Try with all A's first
test = known + "A" * (remaining) + "}"
print(f"Testing: {test}")
print(f"Result: {'true' if test_flag(test) else 'false'}")

# Now brute force each position
flag = list(known + "_" * remaining + "}")

for pos in range(len(known), FLAG_LEN - 1):
    print(f"\nBrute forcing position {pos}...")
    found = False

    for c in charset:
        flag[pos] = c
        test_str = ''.join(flag)

        # We need a special approach - test with the full 41 chars
        # but only check up to current position + some padding

        result = test_flag(test_str)
        if result:
            print(f"Found! Position {pos} = '{c}'")
            found = True
            break

    if not found:
        print(f"No match found for position {pos}!")
        # Continue with the underscore

print(f"\nFinal flag: {''.join(flag)}")
