#!/usr/bin/env python3
"""
Work backwards through the nucleus binary chain to extract the flag.
Each binary's resource contains an XORed version of the previous binary.
The XOR key used at each step is a character of the flag.
"""

import pefile
from io import BytesIO
import re

def extract_xor_key_and_payload(binary_data):
    """Extract XOR key and decrypted payload from binary data."""
    try:
        pe = pefile.PE(data=binary_data, fast_load=False)
        
        if not hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
            return None, None
        
        # Extract custom resource (type 0xa, ID 0x65)
        for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries:
            if entry.struct.Id == 0xa:
                for subentry in entry.directory.entries:
                    if subentry.struct.Id == 0x65:
                        data_rva = subentry.directory.entries[0].data.struct.OffsetToData
                        size = subentry.directory.entries[0].data.struct.Size
                        data = pe.get_data(data_rva, size)
                        
                        # Find XOR key by looking for MZ header pattern
                        for key in range(256):
                            first_bytes = bytes([b ^ key for b in data[:4]])
                            if first_bytes[:2] == b'MZ':
                                decrypted = bytes([b ^ key for b in data])
                                return key, decrypted
        
        return None, None
    except Exception as e:
        return None, None

def solve():
    """Extract the flag by working backwards through the binary chain."""
    flag_chars = []
    start_name = 'nucleus21.exe'
    
    # Load starting binary
    with open(start_name, 'rb') as f:
        current_binary = f.read()
    
    print("[*] Extracting flag from nucleus binary chain...\n")
    
    iteration = 0
    max_iterations = 100
    
    while iteration < max_iterations:
        xor_key, decrypted_payload = extract_xor_key_and_payload(current_binary)
        
        if xor_key is None:
            print(f"[+] Reached root binary (iteration {iteration})")
            break
        
        # Convert key to character
        char = chr(xor_key) if 32 <= xor_key <= 126 else f"?({xor_key:02x})"
        flag_chars.insert(0, char)
        
        print(f"  Stage {iteration}: XOR Key = {xor_key:3d} (0x{xor_key:02x}) = '{char}'")
        
        # Verify and continue with decrypted payload
        if decrypted_payload[:2] != b'MZ':
            print(f"[-] Invalid PE header in decrypted payload")
            break
        
        current_binary = decrypted_payload
        iteration += 1

    # Save the innermost executable with the expected nucleus index.
    # m = re.search(r'(\d+)', start_name)
    # start_index = int(m.group(1)) if m else iteration
    # root_index = max(start_index - iteration, 0)
    # root_name = f'nucleus{root_index}.exe'
    # with open(root_name, 'wb') as f:
    #     f.write(current_binary)
    # print(f"[+] Wrote innermost executable to {root_name}")
    
    flag = ''.join(flag_chars)
    print(f"\n{'='*60}")
    print(f"[+] FLAG: {flag}")
    print(f"{'='*60}\n")
    
    return flag

if __name__ == "__main__":
    solve()
