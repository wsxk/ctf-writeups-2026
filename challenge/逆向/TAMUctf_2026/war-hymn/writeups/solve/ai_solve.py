import ctypes
import tempfile
from pathlib import Path
import zlib

import lief


def rc4(key, data):
	s = list(range(256))
	j = 0
	for i in range(256):
		j = (j + s[i] + key[i % len(key)]) & 0xFF
		s[i], s[j] = s[j], s[i]
	i = 0
	j = 0
	out = bytearray()
	for b in data:
		i = (i + 1) & 0xFF
		j = (j + s[i]) & 0xFF
		s[i], s[j] = s[j], s[i]
		out.append(b ^ s[(s[i] + s[j]) & 0xFF])
	return bytes(out)


def sym_bytes(binary, name, n):
	sym = next(s for s in binary.symbols if s.name == name)
	return bytes(binary.get_content_from_virtual_address(sym.value, n))


root = Path(__file__).resolve().parent.parent
outer = lief.parse(str(root / "war-hymn"))

stage_code = bytes(outer.get_section(".init.checksum.validation").content)
stage_input = bytes(outer.get_section(".bss.secure.buffer").content)
stage_key = bytes(outer.get_section(".init.constructors.global").content)

libc = ctypes.CDLL("libc.so.6")
libc.mmap.restype = ctypes.c_void_p
addr = libc.mmap(None, len(stage_code), 1 | 2 | 4, 2 | 0x20, -1, 0)
ctypes.memmove(addr, stage_code, len(stage_code))

fn = ctypes.CFUNCTYPE(
	None,
	ctypes.c_void_p,
	ctypes.c_size_t,
	ctypes.c_void_p,
	ctypes.c_void_p,
	ctypes.c_size_t,
)(addr)

in_buf = ctypes.create_string_buffer(stage_input)
key_buf = ctypes.create_string_buffer(stage_key)
out_buf = ctypes.create_string_buffer(0x40000)
fn(
	ctypes.cast(in_buf, ctypes.c_void_p),
	len(stage_input),
	ctypes.cast(out_buf, ctypes.c_void_p),
	ctypes.cast(key_buf, ctypes.c_void_p),
	len(stage_key) - 1,
)

raw = out_buf.raw
zlen = int.from_bytes(raw[4:8], "little")
inner_bytes = zlib.decompress(raw[8 : 8 + zlen])

with tempfile.NamedTemporaryFile(suffix=".elf", delete=False) as f:
	f.write(inner_bytes)
	tmp_path = f.name

inner = lief.parse(tmp_path)

key = sym_bytes(inner, "key", 0x12)
msg1 = rc4(key, sym_bytes(inner, "data1", 0x12)).split(b"\x00", 1)[0].decode()
msg2 = rc4(key, sym_bytes(inner, "data2", 0x0F)).split(b"\x00", 1)[0].decode()
msg3 = rc4(key, sym_bytes(inner, "data3", 0x11)).split(b"\x00", 1)[0].decode()
flag = rc4(key, sym_bytes(inner, "DAT_00104110", 0x34)).split(b"\x00", 1)[0].decode()

print(msg1)
print(msg2)
print(msg3)
print(flag)
