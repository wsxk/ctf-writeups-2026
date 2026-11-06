with open('pickled.txt', 'r') as file:
  words = file.read().split()
  bits = "".join(['1' if t == 'pickle' else '0' for t in words])
  encoded_bytes = bytearray()
  for i in range(0, len(bits), 8):
    encoded_bytes.append(int(bits[i:i+8], 2))
  key = 0x67
  elf = bytes([b ^ key for b in encoded_bytes])

  with open('unpickled_elf', 'wb') as file:
    file.write(elf)
