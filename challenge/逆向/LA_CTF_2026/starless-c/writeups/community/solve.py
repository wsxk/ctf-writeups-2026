#!/usr/bin/env python3
"""
Analyze the starless_c maze binary to extract the graph structure.

Each cell has the same code pattern:
- Read input char
- Check if 'w', 'a', 's', 'd', 'f'
- For each direction, check if destination cell's first byte is 0x90
- If 0x90, move there; otherwise crash

The destination addresses are encoded in the cell code at specific offsets.
"""

import struct
from collections import deque

# Read the binary
with open('starless_c', 'rb') as f:
    data = f.read()

# Parse ELF program headers
e_phoff = struct.unpack('<Q', data[0x20:0x28])[0]
e_phentsize = struct.unpack('<H', data[0x36:0x38])[0]
e_phnum = struct.unpack('<H', data[0x38:0x3a])[0]

segments = []
for i in range(e_phnum):
    offset = e_phoff + i * e_phentsize
    p_type = struct.unpack('<I', data[offset:offset+4])[0]
    if p_type == 1:  # PT_LOAD
        p_offset = struct.unpack('<Q', data[offset+8:offset+16])[0]
        p_vaddr = struct.unpack('<Q', data[offset+16:offset+24])[0]
        p_filesz = struct.unpack('<Q', data[offset+32:offset+40])[0]
        p_memsz = struct.unpack('<Q', data[offset+40:offset+48])[0]
        if p_filesz > 0:  # Only include segments with content
            segments.append((p_vaddr, p_offset, p_filesz, p_memsz))

def vaddr_to_offset(vaddr):
    for vaddr_base, file_off, filesz, memsz in segments:
        if vaddr_base <= vaddr < vaddr_base + memsz:
            return file_off + (vaddr - vaddr_base)
    return None

def get_byte_at_vaddr(vaddr):
    off = vaddr_to_offset(vaddr)
    if off is not None and off < len(data):
        return data[off]
    return None

def get_dword_at_vaddr(vaddr):
    off = vaddr_to_offset(vaddr)
    if off is not None and off + 4 <= len(data):
        return struct.unpack('<I', data[off:off+4])[0]
    return None

def get_qword_at_vaddr(vaddr):
    off = vaddr_to_offset(vaddr)
    if off is not None and off + 8 <= len(data):
        return struct.unpack('<Q', data[off:off+8])[0]
    return None

# Collect all maze cell addresses from program headers
# Cells are in the 0x676xxxxx range
maze_cells = []
for vaddr, foff, fsz, msz in segments:
    if 0x67670000 <= vaddr < 0x676b0000 and fsz > 0:
        maze_cells.append(vaddr)

maze_cells = sorted(set(maze_cells))
print(f"Found {len(maze_cells)} potential maze cells:")
for cell in maze_cells:
    first_byte = get_byte_at_vaddr(cell)
    status = "ACTIVE" if first_byte == 0x90 else f"inactive (0x{first_byte:02x})"
    print(f"  {cell:#x}: {status}")

# Now let's find the transitions by analyzing the cell code
# Each cell's code checks destinations for 'w', 'a', 's', 'd' directions
# The pattern is: check data_XXXXXXXX, if byte == 0x90, move there

# From the decompilation, we can see patterns like:
# 6767905b        int32_t rax_3 = data_67681000
# This means 's' from cell 0x67679000 leads to 0x67681000

# Let's extract the graph by analyzing the binary code
# The pattern for reading a destination address seems to be:
# 8b 05 XX XX XX XX  = mov eax, [rip+XX]
# where XX XX XX XX is a signed 32-bit offset

def analyze_cell_transitions(cell_addr):
    """Analyze a cell to find where each direction leads."""
    off = vaddr_to_offset(cell_addr)
    if off is None:
        return None

    # Read 256 bytes of cell code
    cell_code = data[off:off+256] if off + 256 <= len(data) else data[off:]

    transitions = {}

    # Look for patterns like: 8b 05 XX XX XX XX (mov eax, [rip+offset])
    # followed by comparison and jump patterns
    for i in range(len(cell_code) - 10):
        # Pattern: 8b 05 XX XX XX XX = mov eax, [rip+offset]
        if cell_code[i:i+2] == b'\x8b\x05':
            rip_offset = struct.unpack('<i', cell_code[i+2:i+6])[0]
            # RIP is at i+6 (after the instruction)
            target_addr = cell_addr + i + 6 + rip_offset

            # Now look backwards to see which direction this is for
            # The pattern is: 3c XX = cmp al, char; 74 XX = jz offset
            if i >= 4 and cell_code[i-2] == 0x74:  # jz
                if cell_code[i-4:i-3] == b'\x3c':  # cmp al, imm8
                    direction_char = cell_code[i-3]
                    if direction_char in [0x77, 0x61, 0x73, 0x64]:  # w, a, s, d
                        dir_name = chr(direction_char)
                        transitions[dir_name] = target_addr

    return transitions

print("\n\nAnalyzing cell transitions:")
start_cell = 0x67679000
print(f"\nStarting cell: {start_cell:#x}")

# The maze graph
graph = {}

# BFS through all reachable cells
visited = set()
queue = deque([start_cell])

while queue:
    cell = queue.popleft()
    if cell in visited:
        continue
    visited.add(cell)

    first_byte = get_byte_at_vaddr(cell)
    if first_byte is None:
        continue

    trans = analyze_cell_transitions(cell)
    if trans:
        graph[cell] = trans
        print(f"\nCell {cell:#x} (byte={first_byte:#04x}):")
        for d, target in sorted(trans.items()):
            target_byte = get_byte_at_vaddr(target)
            status = "REACHABLE" if target_byte == 0x90 else f"blocked (0x{target_byte:02x})" if target_byte else "unmapped"
            print(f"  '{d}' -> {target:#x} ({status})")

            # Only queue cells that are reachable (first byte == 0x90)
            if target_byte == 0x90 and target not in visited:
                queue.append(target)

print("\n\n=== MAZE GRAPH (reachable cells only) ===")
# Now find the path through the maze
# Start from 0x67679000, find path to... where?
# The 'f' command leads to the flag. We need to find which cell allows 'f'.

# Looking at the decompilation, 'f' leads to label_6767a002 which then does:
# 42069133: print message and read flag

# Let's find the path using BFS
def find_flag_path():
    """BFS to find path from start to a cell where 'f' is valid."""
    queue = deque([(start_cell, "")])
    visited = {start_cell}

    while queue:
        cell, path = queue.popleft()

        if cell not in graph:
            continue

        trans = graph[cell]
        for d, target in trans.items():
            target_byte = get_byte_at_vaddr(target)

            if target_byte == 0x90:  # Can move to this cell
                new_path = path + d
                if target not in visited:
                    visited.add(target)
                    queue.append((target, new_path))
                    print(f"Path '{new_path}' leads to {target:#x}")

        # Check if we've reached a cell where no further moves are possible
        # but 'f' might work
        reachable = [t for d, t in trans.items() if get_byte_at_vaddr(t) == 0x90]
        if not reachable:
            print(f"\nDead end at {cell:#x} with path: {path}")
            print(f"  Let's try 'f' here: path = '{path}f'")
            return path + 'f'

    return None

print("\nSearching for flag path...")
flag_path = find_flag_path()
if flag_path:
    print(f"\nPotential flag path: '{flag_path}'")
