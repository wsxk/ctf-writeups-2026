#!/usr/bin/env python3
import argparse
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import ctypes
import mmap
import os
import pathlib
import re
import struct
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass

from elftools.elf.elffile import ELFFile
from unicorn import Uc, UcError
from unicorn import UC_ARCH_X86, UC_HOOK_CODE, UC_HOOK_INSN_INVALID, UC_HOOK_MEM_WRITE, UC_MODE_64
from unicorn.x86_const import (
    UC_CPU_X86_SKYLAKE_CLIENT,
    UC_X86_REG_EFLAGS,
    UC_X86_REG_XMM0,
    UC_X86_REG_XMM1,
    UC_X86_REG_XMM2,
    UC_X86_REG_XMM3,
    UC_X86_REG_XMM4,
    UC_X86_REG_XMM5,
    UC_X86_REG_XMM6,
    UC_X86_REG_XMM7,
    UC_X86_REG_R8,
    UC_X86_REG_R9,
    UC_X86_REG_R10,
    UC_X86_REG_R11,
    UC_X86_REG_R12,
    UC_X86_REG_R13,
    UC_X86_REG_R14,
    UC_X86_REG_R15,
    UC_X86_REG_RAX,
    UC_X86_REG_RBP,
    UC_X86_REG_RBX,
    UC_X86_REG_RCX,
    UC_X86_REG_RDI,
    UC_X86_REG_RDX,
    UC_X86_REG_RIP,
    UC_X86_REG_RSI,
    UC_X86_REG_RSP,
)

TOKEN_RE = re.compile(r"token to get the flag:\s*([0-9a-fA-F]+)")
LEGACY_MAIN_PATTERN = b"\x48\x81\xec\x08\x10\x00\x00\x31\xff\xe8"

# Fixed VM layout for emulation.
STACK_BASE = 0x70000000
STACK_SIZE = 0x20000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000
INITIAL_RDI = STACK_TOP - 0x2000

# Mutable data region used by onion stages.
DATA_RESTORE_LO = 0x459000
DATA_RESTORE_HI = 0x459200

EMULATE_UNSUPPORTED_SHA_NATIVE = os.getenv("ONION_SHA_NATIVE_EMU", "0") == "1"
_SHA_HELPER_FN = None

XMM_REGS = [
    UC_X86_REG_XMM0,
    UC_X86_REG_XMM1,
    UC_X86_REG_XMM2,
    UC_X86_REG_XMM3,
    UC_X86_REG_XMM4,
    UC_X86_REG_XMM5,
    UC_X86_REG_XMM6,
    UC_X86_REG_XMM7,
]

REGISTERS = [
    UC_X86_REG_RAX,
    UC_X86_REG_RBX,
    UC_X86_REG_RCX,
    UC_X86_REG_RDX,
    UC_X86_REG_RSI,
    UC_X86_REG_RDI,
    UC_X86_REG_RBP,
    UC_X86_REG_RSP,
    UC_X86_REG_R8,
    UC_X86_REG_R9,
    UC_X86_REG_R10,
    UC_X86_REG_R11,
    UC_X86_REG_R12,
    UC_X86_REG_R13,
    UC_X86_REG_R14,
    UC_X86_REG_R15,
    UC_X86_REG_RIP,
    UC_X86_REG_EFLAGS,
]


def align_down(value: int, align: int) -> int:
    return value & ~(align - 1)


def align_up(value: int, align: int) -> int:
    return (value + align - 1) & ~(align - 1)


def _build_native_sha_helper():
    global _SHA_HELPER_FN
    if _SHA_HELPER_FN is not None:
        return _SHA_HELPER_FN

    helper_c = r"""
#include <immintrin.h>
#include <stdint.h>

__attribute__((target("sha")))
void sha256rnds2_step(const uint8_t *dst_in,
                      const uint8_t *src_in,
                      const uint8_t *x0_in,
                      uint8_t *dst_out) {
  __m128i d = _mm_loadu_si128((const __m128i *)dst_in);
  __m128i s = _mm_loadu_si128((const __m128i *)src_in);
  __m128i x0 = _mm_loadu_si128((const __m128i *)x0_in);
  d = _mm_sha256rnds2_epu32(d, s, x0);
  _mm_storeu_si128((__m128i *)dst_out, d);
}
"""
    tmpdir = pathlib.Path(tempfile.gettempdir())
    src_path = tmpdir / "onion_sha_helper.c"
    so_path = tmpdir / "onion_sha_helper.so"
    src_path.write_text(helper_c)
    subprocess.run(
        [
            "clang",
            "-O3",
            "-shared",
            "-fPIC",
            "-msha",
            "-o",
            str(so_path),
            str(src_path),
        ],
        check=True,
    )
    lib = ctypes.CDLL(str(so_path))
    fn = lib.sha256rnds2_step
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
    ]
    fn.restype = None
    _SHA_HELPER_FN = fn
    return _SHA_HELPER_FN


def _emulate_sha256rnds2_with_native(mu: Uc) -> bool:
    rip = mu.reg_read(UC_X86_REG_RIP)
    insn = bytes(mu.mem_read(rip, 4))
    if len(insn) < 4 or insn[0] != 0x0F or insn[1] != 0x38 or insn[2] != 0xCB:
        return False
    modrm = insn[3]
    mod = (modrm >> 6) & 0x3
    reg = (modrm >> 3) & 0x7
    rm = modrm & 0x7
    if mod != 0x3:
        # Only register form is emitted by our generator.
        return False

    dst_reg = XMM_REGS[reg]
    src_reg = XMM_REGS[rm]
    x0_reg = UC_X86_REG_XMM0

    dst_bytes = (mu.reg_read(dst_reg) & ((1 << 128) - 1)).to_bytes(16, "little")
    src_bytes = (mu.reg_read(src_reg) & ((1 << 128) - 1)).to_bytes(16, "little")
    x0_bytes = (mu.reg_read(x0_reg) & ((1 << 128) - 1)).to_bytes(16, "little")

    dst_in = (ctypes.c_uint8 * 16).from_buffer_copy(dst_bytes)
    src_in = (ctypes.c_uint8 * 16).from_buffer_copy(src_bytes)
    x0_in = (ctypes.c_uint8 * 16).from_buffer_copy(x0_bytes)
    dst_out = (ctypes.c_uint8 * 16)()
    _build_native_sha_helper()(dst_in, src_in, x0_in, dst_out)
    out = bytes(dst_out)
    mu.reg_write(dst_reg, int.from_bytes(out, "little"))
    mu.reg_write(UC_X86_REG_RIP, rip + 4)
    return True


def run_binary(binary: pathlib.Path, key_bytes: bytes, timeout: int) -> tuple[int, str, str]:
    proc = subprocess.run(
        [str(binary.resolve())],
        input=key_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    return proc.returncode, proc.stdout.decode(errors="replace"), proc.stderr.decode(errors="replace")


def extract_token(stdout: str) -> str | None:
    m = TOKEN_RE.search(stdout)
    return m.group(1) if m else None


@dataclass
class BinaryInfo:
    path: pathlib.Path
    segments: list[tuple[int, bytes, int]]
    map_base: int
    map_size: int
    text_lo: int
    text_hi: int
    stage_entry: int
    plt_putchar: int
    plt_read: int
    plt_mprotect: int


@dataclass
class Snapshot:
    regs: dict[int, int]
    code: bytes
    stack: bytes


def parse_binary_info(path: pathlib.Path) -> BinaryInfo:
    segments: list[tuple[int, bytes, int]] = []
    with path.open("rb") as f:
        elf = ELFFile(f)
        text = elf.get_section_by_name(".text")
        if text is None:
            raise RuntimeError("ELF has no .text section")
        plt = elf.get_section_by_name(".plt")
        if plt is None:
            raise RuntimeError("ELF has no .plt section")
        text_lo = int(text["sh_addr"])
        text_data = text.data()
        text_hi = text_lo + int(text["sh_size"])
        plt_base = int(plt["sh_addr"])
        lo = 1 << 64
        hi = 0
        for seg in elf.iter_segments():
            if seg["p_type"] != "PT_LOAD":
                continue
            vaddr = int(seg["p_vaddr"])
            data = seg.data()
            memsz = int(seg["p_memsz"])
            segments.append((vaddr, data, memsz))
            lo = min(lo, vaddr)
            hi = max(hi, vaddr + memsz)
    if not segments:
        raise RuntimeError("No PT_LOAD segments found")
    map_base = align_down(lo, 0x1000)
    map_size = align_up(hi, 0x1000) - map_base

    stage_entry = None

    # Legacy C-generated main() signature.
    idx = 0
    while True:
        idx = text_data.find(LEGACY_MAIN_PATTERN, idx)
        if idx < 0:
            break
        rel = struct.unpack_from("<i", text_data, idx + 10)[0]
        target = text_lo + idx + 14 + rel
        off = target - text_lo
        if 0 <= off + 3 <= len(text_data) and text_data[off : off + 3] == b"\x48\x85\xff":
            stage_entry = target
            break
        idx += 1

    # Assembly-generated main(): scan for `xor edi,edi; call <run>`, where run starts with `test rdi,rdi`.
    if stage_entry is None:
        for idx in range(0, len(text_data) - 8):
            if text_data[idx : idx + 2] != b"\x31\xff":
                continue
            if text_data[idx + 2] != 0xE8:
                continue
            rel = struct.unpack_from("<i", text_data, idx + 3)[0]
            target = text_lo + idx + 7 + rel
            off = target - text_lo
            if 0 <= off + 3 <= len(text_data) and text_data[off : off + 3] == b"\x48\x85\xff":
                stage_entry = target
                break

    if stage_entry is None:
        raise RuntimeError("Unable to locate onion stage entry")

    # In this challenge's binaries, imported symbols are always [putchar, read, mprotect].
    plt_putchar = plt_base + 0x10
    plt_read = plt_base + 0x20
    plt_mprotect = plt_base + 0x30
    return BinaryInfo(
        path=path,
        segments=segments,
        map_base=map_base,
        map_size=map_size,
        text_lo=text_lo,
        text_hi=text_hi,
        stage_entry=stage_entry,
        plt_putchar=plt_putchar,
        plt_read=plt_read,
        plt_mprotect=plt_mprotect,
    )


def build_uc(info: BinaryInfo, snapshot: Snapshot | None = None) -> Uc:
    mu = Uc(UC_ARCH_X86, UC_MODE_64)
    # Required for AES/BMI2/etc instruction support in this challenge.
    try:
        mu.ctl_set_cpu_model(UC_CPU_X86_SKYLAKE_CLIENT)
    except Exception:
        pass
    mu.mem_map(info.map_base, info.map_size)
    if snapshot is None:
        for vaddr, data, memsz in info.segments:
            mu.mem_write(vaddr, data)
            if memsz > len(data):
                mu.mem_write(vaddr + len(data), b"\x00" * (memsz - len(data)))
        mu.mem_map(STACK_BASE, STACK_SIZE)
        mu.reg_write(UC_X86_REG_RSP, STACK_TOP)
        mu.reg_write(UC_X86_REG_RDI, INITIAL_RDI)
        mu.reg_write(UC_X86_REG_RIP, info.stage_entry)
    else:
        mu.mem_write(info.map_base, snapshot.code)
        mu.mem_map(STACK_BASE, STACK_SIZE)
        mu.mem_write(STACK_BASE, snapshot.stack)
        for reg, value in snapshot.regs.items():
            mu.reg_write(reg, value)

    if EMULATE_UNSUPPORTED_SHA_NATIVE:
        def hook_invalid(mu_: Uc, _user: object) -> bool:
            return _emulate_sha256rnds2_with_native(mu_)

        mu.hook_add(UC_HOOK_INSN_INVALID, hook_invalid)
    return mu


def read_regs(mu: Uc) -> dict[int, int]:
    return {reg: mu.reg_read(reg) for reg in REGISTERS}


def capture_snapshot(mu: Uc, info: BinaryInfo) -> Snapshot:
    return Snapshot(
        regs=read_regs(mu),
        code=bytes(mu.mem_read(info.map_base, info.map_size)),
        stack=bytes(mu.mem_read(STACK_BASE, STACK_SIZE)),
    )


def do_ret(mu: Uc) -> None:
    rsp = mu.reg_read(UC_X86_REG_RSP)
    ret = struct.unpack("<Q", mu.mem_read(rsp, 8))[0]
    mu.reg_write(UC_X86_REG_RSP, rsp + 8)
    mu.reg_write(UC_X86_REG_RIP, ret)


def get_stage0_first_read_snapshot(info: BinaryInfo) -> Snapshot:
    mu = build_uc(info)
    state = {"seen": False}

    def hook_read(mu_: Uc, _addr: int, _size: int, _user: object) -> None:
        state["seen"] = True
        mu_.emu_stop()

    def hook_putchar(mu_: Uc, _addr: int, _size: int, _user: object) -> None:
        mu_.reg_write(UC_X86_REG_RAX, mu_.reg_read(UC_X86_REG_RDI) & 0xFF)
        do_ret(mu_)

    def hook_mprotect(mu_: Uc, _addr: int, _size: int, _user: object) -> None:
        mu_.reg_write(UC_X86_REG_RAX, 0)
        do_ret(mu_)

    mu.hook_add(UC_HOOK_CODE, hook_read, begin=info.plt_read, end=info.plt_read)
    mu.hook_add(UC_HOOK_CODE, hook_putchar, begin=info.plt_putchar, end=info.plt_putchar)
    mu.hook_add(UC_HOOK_CODE, hook_mprotect, begin=info.plt_mprotect, end=info.plt_mprotect)
    mu.emu_start(info.stage_entry, 0, count=20_000_000)
    if not state["seen"]:
        raise RuntimeError("Failed to reach stage0 first read")
    return capture_snapshot(mu, info)


def probe_target_range(info: BinaryInfo, snapshot: Snapshot) -> tuple[int, int]:
    mu = build_uc(info, snapshot)
    state = {"read_idx": 0, "wstart": None, "wmax": None, "wcount": 0}

    def hook_read(mu_: Uc, _addr: int, _size: int, _user: object) -> None:
        fd = mu_.reg_read(UC_X86_REG_RDI)
        buf = mu_.reg_read(UC_X86_REG_RSI)
        cnt = mu_.reg_read(UC_X86_REG_RDX)
        if fd == 0 and cnt == 1:
            byte = 0
            mu_.mem_write(buf, bytes([byte]))
            mu_.reg_write(UC_X86_REG_RAX, 1)
            state["read_idx"] += 1
        else:
            mu_.reg_write(UC_X86_REG_RAX, 0)
        do_ret(mu_)

    def hook_putchar(mu_: Uc, _addr: int, _size: int, _user: object) -> None:
        mu_.reg_write(UC_X86_REG_RAX, mu_.reg_read(UC_X86_REG_RDI) & 0xFF)
        do_ret(mu_)

    def hook_mprotect(mu_: Uc, _addr: int, _size: int, _user: object) -> None:
        mu_.reg_write(UC_X86_REG_RAX, 0)
        do_ret(mu_)

    def hook_write(mu_: Uc, _access: int, addr: int, size: int, _value: int, _user: object) -> None:
        if not (info.text_lo <= addr < info.text_hi):
            return
        if state["wstart"] is None or addr < state["wstart"]:
            state["wstart"] = addr
        hi = addr + size - 1
        if state["wmax"] is None or hi > state["wmax"]:
            state["wmax"] = hi
        state["wcount"] += 1

    def hook_code(mu_: Uc, addr: int, _size: int, _user: object) -> None:
        if (
            state["wstart"] is not None
            and state["read_idx"] >= 2
            and state["wcount"] > 8
            and addr == state["wstart"]
        ):
            mu_.emu_stop()

    mu.hook_add(UC_HOOK_CODE, hook_read, begin=info.plt_read, end=info.plt_read)
    mu.hook_add(UC_HOOK_CODE, hook_putchar, begin=info.plt_putchar, end=info.plt_putchar)
    mu.hook_add(UC_HOOK_CODE, hook_mprotect, begin=info.plt_mprotect, end=info.plt_mprotect)
    mu.hook_add(UC_HOOK_MEM_WRITE, hook_write, begin=info.text_lo, end=info.text_hi - 1)
    mu.hook_add(UC_HOOK_CODE, hook_code)
    try:
        mu.emu_start(snapshot.regs[UC_X86_REG_RIP], 0, count=8_000_000)
    except UcError:
        pass
    if state["wstart"] is None or state["wmax"] is None:
        raise RuntimeError("Probe failed: no text writes observed")
    return state["wstart"], state["wmax"] + 1


class PrefixScanner:
    def __init__(self, info: BinaryInfo, snapshot: Snapshot, target_start: int, prefix_len: int) -> None:
        self.info = info
        self.target_start = target_start
        self.prefix_len = prefix_len
        self.mu = build_uc(info, snapshot)
        self.stage_rip = snapshot.regs[UC_X86_REG_RIP]
        self.ctx = self.mu.context_save()

        self.data_lo = max(info.map_base, DATA_RESTORE_LO)
        self.data_hi = min(info.map_base + info.map_size, DATA_RESTORE_HI)
        if self.data_hi > self.data_lo:
            self.data_base = bytes(self.mu.mem_read(self.data_lo, self.data_hi - self.data_lo))
        else:
            self.data_lo = info.map_base
            self.data_hi = info.map_base
            self.data_base = b""

        rsp = snapshot.regs[UC_X86_REG_RSP]
        self.stack_lo = max(STACK_BASE, rsp - 0x200)
        self.stack_hi = min(STACK_BASE + STACK_SIZE, rsp + 0x300)
        self.stack_base = bytes(self.mu.mem_read(self.stack_lo, self.stack_hi - self.stack_lo))

        self.prefix_base = bytes(self.mu.mem_read(target_start, prefix_len))
        self.state = {"cand": 0, "read_idx": 0, "writes": 0}

        self.mu.hook_add(UC_HOOK_CODE, self._hook_read, begin=info.plt_read, end=info.plt_read)
        self.mu.hook_add(UC_HOOK_CODE, self._hook_putchar, begin=info.plt_putchar, end=info.plt_putchar)
        self.mu.hook_add(UC_HOOK_CODE, self._hook_mprotect, begin=info.plt_mprotect, end=info.plt_mprotect)
        self.mu.hook_add(
            UC_HOOK_MEM_WRITE,
            self._hook_write,
            begin=target_start,
            end=target_start + prefix_len - 1,
        )

    def _hook_read(self, mu: Uc, _addr: int, _size: int, _user: object) -> None:
        fd = mu.reg_read(UC_X86_REG_RDI)
        buf = mu.reg_read(UC_X86_REG_RSI)
        cnt = mu.reg_read(UC_X86_REG_RDX)
        if fd == 0 and cnt == 1:
            cand = self.state["cand"]
            byte = (cand & 0xFF) if self.state["read_idx"] == 0 else ((cand >> 8) & 0xFF)
            mu.mem_write(buf, bytes([byte]))
            mu.reg_write(UC_X86_REG_RAX, 1)
            self.state["read_idx"] += 1
        else:
            mu.reg_write(UC_X86_REG_RAX, 0)
        do_ret(mu)

    def _hook_putchar(self, mu: Uc, _addr: int, _size: int, _user: object) -> None:
        mu.reg_write(UC_X86_REG_RAX, mu.reg_read(UC_X86_REG_RDI) & 0xFF)
        do_ret(mu)

    def _hook_mprotect(self, mu: Uc, _addr: int, _size: int, _user: object) -> None:
        mu.reg_write(UC_X86_REG_RAX, 0)
        do_ret(mu)

    def _hook_write(self, mu: Uc, _access: int, _addr: int, _size: int, _value: int, _user: object) -> None:
        self.state["writes"] += 1
        if self.state["writes"] >= self.prefix_len:
            mu.emu_stop()

    def run_candidate(self, cand: int) -> bytes:
        self.state["cand"] = cand
        self.state["read_idx"] = 0
        self.state["writes"] = 0

        self.mu.context_restore(self.ctx)
        if self.data_base:
            self.mu.mem_write(self.data_lo, self.data_base)
        self.mu.mem_write(self.stack_lo, self.stack_base)
        self.mu.mem_write(self.target_start, self.prefix_base)
        try:
            self.mu.emu_start(self.stage_rip, 0, count=600_000)
        except UcError:
            pass
        return bytes(self.mu.mem_read(self.target_start, self.prefix_len))


def plausible_strict(prefix: bytes) -> bool:
    if len(prefix) < 6:
        return False
    b0 = prefix[0]
    if (
        0xB8 <= b0 <= 0xBF
        and prefix[2] == 0
        and prefix[3] == 0
        and prefix[4] == 0
        and 0x08 <= prefix[1] <= 0x30
        and prefix[5] in (0x31, 0x69, 0x81, 0x0F, 0x66, 0x48)
    ):
        return True
    if (
        0x40 <= b0 <= 0x4F
        and len(prefix) >= 8
        and prefix[1] == 0x31
        and 0xB8 <= prefix[3] <= 0xBF
        and prefix[6] == 0
        and prefix[7] == 0
    ):
        return True
    if b0 == 0x31 and prefix[1] in (0xC9, 0xD2, 0xF6, 0xFF, 0xC0) and prefix[2] in (0x31, 0xB8, 0x66, 0x69, 0x83, 0x0F):
        return True
    return False


def plausible_relaxed(prefix: bytes) -> bool:
    if len(prefix) < 5:
        return False
    b0 = prefix[0]
    if 0xB8 <= b0 <= 0xBF:
        return prefix[2] == 0 and prefix[3] == 0 and prefix[4] == 0
    if b0 == 0x31:
        return True
    if 0x40 <= b0 <= 0x4F and len(prefix) >= 4:
        return prefix[1] in (0x31, 0x8D, 0x89, 0x8B, 0x69, 0x81, 0x83)
    return False


def plausible_wide(prefix: bytes) -> bool:
    if plausible_relaxed(prefix):
        return True
    if len(prefix) < 2:
        return False
    b0 = prefix[0]
    if b0 in (0x48, 0x66, 0x69, 0x81, 0x83, 0x0F):
        # Keep this broad but avoid obviously bad dense-noise starts.
        return prefix[1] not in (0x00, 0xFF)
    return False


def _classify_worker(
    info: BinaryInfo,
    snapshot: Snapshot,
    target_start: int,
    prefix_len: int,
    worker_id: int,
    workers: int,
) -> tuple[list[int], list[int], list[int]]:
    scanner = PrefixScanner(info, snapshot, target_start, prefix_len)
    strict_local: list[int] = []
    relaxed_local: list[int] = []
    wide_local: list[int] = []
    for cand in range(worker_id, 65536, workers):
        pref = scanner.run_candidate(cand)
        if plausible_strict(pref):
            strict_local.append(cand)
        elif plausible_relaxed(pref):
            relaxed_local.append(cand)
        elif plausible_wide(pref):
            wide_local.append(cand)
    return strict_local, relaxed_local, wide_local


def _classify_worker_process(args: tuple[BinaryInfo, Snapshot, int, int, int, int]) -> tuple[list[int], list[int], list[int]]:
    info, snapshot, target_start, prefix_len, worker_id, workers = args
    return _classify_worker(info, snapshot, target_start, prefix_len, worker_id, workers)


def classify_candidates_parallel(
    info: BinaryInfo,
    snapshot: Snapshot,
    target_start: int,
    prefix_len: int,
    workers: int,
    backend: str,
) -> tuple[list[int], list[int], list[int]]:
    workers = max(1, workers)
    strict_candidates: list[int] = []
    relaxed_candidates: list[int] = []
    wide_candidates: list[int] = []
    if workers == 1:
        strict_local, relaxed_local, wide_local = _classify_worker(
            info=info,
            snapshot=snapshot,
            target_start=target_start,
            prefix_len=prefix_len,
            worker_id=0,
            workers=1,
        )
        strict_candidates.extend(strict_local)
        relaxed_candidates.extend(relaxed_local)
        wide_candidates.extend(wide_local)
    elif backend == "thread":
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(
                    _classify_worker,
                    info,
                    snapshot,
                    target_start,
                    prefix_len,
                    worker_id,
                    workers,
                )
                for worker_id in range(workers)
            ]
            for fut in futures:
                strict_local, relaxed_local, wide_local = fut.result()
                strict_candidates.extend(strict_local)
                relaxed_candidates.extend(relaxed_local)
                wide_candidates.extend(wide_local)
    elif backend == "process":
        with ProcessPoolExecutor(max_workers=workers) as executor:
            args = [
                (info, snapshot, target_start, prefix_len, worker_id, workers)
                for worker_id in range(workers)
            ]
            for strict_local, relaxed_local, wide_local in executor.map(_classify_worker_process, args):
                strict_candidates.extend(strict_local)
                relaxed_candidates.extend(relaxed_local)
                wide_candidates.extend(wide_local)
    else:
        raise RuntimeError(f"Unknown scan backend: {backend}")

    strict_candidates.sort()
    relaxed_candidates.sort()
    wide_candidates.sort()
    return strict_candidates, relaxed_candidates, wide_candidates


def oracle_try_candidate(
    info: BinaryInfo,
    snapshot: Snapshot,
    candidate: int,
    expect_next_read: bool,
    insn_limit_override: int | None = None,
) -> tuple[bool, Snapshot | None, str]:
    mu = build_uc(info, snapshot)
    state = {"read_idx": 0, "reads_total": 0, "next_read": False, "out": bytearray()}

    def hook_read(mu_: Uc, _addr: int, _size: int, _user: object) -> None:
        fd = mu_.reg_read(UC_X86_REG_RDI)
        buf = mu_.reg_read(UC_X86_REG_RSI)
        cnt = mu_.reg_read(UC_X86_REG_RDX)
        if fd == 0 and cnt == 1:
            state["reads_total"] += 1
            if expect_next_read and state["reads_total"] >= 3:
                state["next_read"] = True
                mu_.emu_stop()
                return
            byte = (candidate & 0xFF) if state["read_idx"] == 0 else ((candidate >> 8) & 0xFF)
            mu_.mem_write(buf, bytes([byte]))
            mu_.reg_write(UC_X86_REG_RAX, 1)
            state["read_idx"] += 1
        else:
            mu_.reg_write(UC_X86_REG_RAX, 0)
        do_ret(mu_)

    def hook_putchar(mu_: Uc, _addr: int, _size: int, _user: object) -> None:
        c = mu_.reg_read(UC_X86_REG_RDI) & 0xFF
        state["out"].append(c)
        mu_.reg_write(UC_X86_REG_RAX, c)
        do_ret(mu_)

    def hook_mprotect(mu_: Uc, _addr: int, _size: int, _user: object) -> None:
        mu_.reg_write(UC_X86_REG_RAX, 0)
        do_ret(mu_)

    mu.hook_add(UC_HOOK_CODE, hook_read, begin=info.plt_read, end=info.plt_read)
    mu.hook_add(UC_HOOK_CODE, hook_putchar, begin=info.plt_putchar, end=info.plt_putchar)
    mu.hook_add(UC_HOOK_CODE, hook_mprotect, begin=info.plt_mprotect, end=info.plt_mprotect)
    if insn_limit_override is not None:
        insn_limit = insn_limit_override
    else:
        insn_limit = 6_000_000 if expect_next_read else 40_000_000
    try:
        mu.emu_start(snapshot.regs[UC_X86_REG_RIP], 0, count=insn_limit)
    except UcError:
        pass

    out = state["out"].decode(errors="replace")
    if expect_next_read:
        if not state["next_read"]:
            return False, None, out
        return True, capture_snapshot(mu, info), out
    # Final stage check: token must be present in output.
    return extract_token(out) is not None, None, out


def recover_key_and_token(
    info: BinaryInfo,
    key_len: int,
    save_key_path: pathlib.Path | None,
    max_stages: int | None,
    known_words: list[int] | None = None,
    scan_workers: int = 16,
    scan_backend: str = "process",
) -> tuple[bytes, str]:
    if key_len % 2 != 0:
        raise RuntimeError("Key length must be even")
    full_stages = key_len // 2
    total_stages = full_stages
    if max_stages is not None:
        total_stages = min(total_stages, max_stages)

    if known_words is None:
        known_words = []
    words: list[int] = list(known_words)
    snapshot = get_stage0_first_read_snapshot(info)
    for idx, word in enumerate(words):
        ok, next_snapshot, _out = oracle_try_candidate(info, snapshot, word, expect_next_read=True)
        if not ok:
            # Late stages may require a much larger instruction budget to hit next read.
            ok, next_snapshot, _out = oracle_try_candidate(
                info,
                snapshot,
                word,
                expect_next_read=True,
                insn_limit_override=40_000_000,
            )
        if not ok or next_snapshot is None:
            raise RuntimeError(f"Failed to resume at known word index {idx}")
        snapshot = next_snapshot

    token = None

    for stage_idx in range(len(words), total_stages):
        expect_next_read = stage_idx < full_stages - 1
        target_start, target_end = probe_target_range(info, snapshot)
        target_len = target_end - target_start
        oracle_limit = 40_000_000 if target_len >= 1200 else 6_000_000

        print(
            f"[stage {stage_idx + 1}/{total_stages}] "
            f"rip={snapshot.regs[UC_X86_REG_RIP]:#x} target=[{target_start:#x},{target_end:#x}) len={target_len}",
            flush=True,
        )

        found_word = None
        found_snapshot = None
        scan_started = time.time()
        strict_candidates, relaxed_candidates, wide_candidates = classify_candidates_parallel(
            info=info,
            snapshot=snapshot,
            target_start=target_start,
            prefix_len=8,
            workers=scan_workers,
            backend=scan_backend,
        )
        scan_elapsed = time.time() - scan_started
        print(
            f"  scanner backend={scan_backend} workers={scan_workers} strict={len(strict_candidates)} "
            f"relaxed={len(relaxed_candidates)} wide={len(wide_candidates)} "
            f"time={scan_elapsed:.2f}s",
            flush=True,
        )

        # Strict pass.
        for idx, cand in enumerate(strict_candidates, 1):
            if idx % 8192 == 0:
                print(f"  strict oracle checked {idx}/{len(strict_candidates)}", flush=True)
            ok, next_snapshot, out = oracle_try_candidate(
                info,
                snapshot,
                cand,
                expect_next_read,
                insn_limit_override=oracle_limit if expect_next_read else None,
            )
            if ok:
                found_word = cand
                found_snapshot = next_snapshot
                token = extract_token(out) or token
                break

        # Relaxed pass.
        if found_word is None:
            print("  strict pass failed; trying relaxed prefix filter", flush=True)
            for idx, cand in enumerate(relaxed_candidates, 1):
                if idx % 8192 == 0:
                    print(f"  relaxed oracle checked {idx}/{len(relaxed_candidates)}", flush=True)
                ok, next_snapshot, out = oracle_try_candidate(
                    info,
                    snapshot,
                    cand,
                    expect_next_read,
                    insn_limit_override=oracle_limit if expect_next_read else None,
                )
                if ok:
                    found_word = cand
                    found_snapshot = next_snapshot
                    token = extract_token(out) or token
                    break

        # Full fallback.
        if found_word is None:
            print("  relaxed pass failed; trying wide prefix filter", flush=True)
            for idx, cand in enumerate(wide_candidates, 1):
                if idx % 8192 == 0:
                    print(f"  wide oracle checked {idx}/{len(wide_candidates)}", flush=True)
                ok, next_snapshot, out = oracle_try_candidate(
                    info,
                    snapshot,
                    cand,
                    expect_next_read,
                    insn_limit_override=oracle_limit if expect_next_read else None,
                )
                if ok:
                    found_word = cand
                    found_snapshot = next_snapshot
                    token = extract_token(out) or token
                    break

        # Full fallback.
        if found_word is None:
            print("  relaxed pass failed; falling back to full oracle brute-force", flush=True)
            already_tested = set(strict_candidates)
            already_tested.update(relaxed_candidates)
            already_tested.update(wide_candidates)
            for cand in range(65536):
                if cand in already_tested:
                    continue
                if cand % 8192 == 0 and cand != 0:
                    print(f"  fallback scan progressed to cand={cand:#06x}", flush=True)
                ok, next_snapshot, out = oracle_try_candidate(
                    info,
                    snapshot,
                    cand,
                    expect_next_read,
                    insn_limit_override=oracle_limit if expect_next_read else None,
                )
                if ok:
                    found_word = cand
                    found_snapshot = next_snapshot
                    token = extract_token(out) or token
                    break

        if found_word is None:
            raise RuntimeError(f"Failed to solve stage {stage_idx}")

        words.append(found_word)
        print(f"  solved word={found_word:#06x}", flush=True)

        if save_key_path is not None:
            partial = b"".join(struct.pack("<H", w) for w in words)
            if len(partial) < key_len:
                partial += b"\x00" * (key_len - len(partial))
            save_key_path.write_bytes(partial)

        if expect_next_read:
            if found_snapshot is None:
                raise RuntimeError("Internal error: missing next snapshot")
            snapshot = found_snapshot

    key_bytes = b"".join(struct.pack("<H", w) for w in words)
    if len(key_bytes) < key_len:
        key_bytes += b"\x00" * (key_len - len(key_bytes))
    if save_key_path is not None:
        save_key_path.write_bytes(key_bytes)
    if token is None and total_stages == full_stages:
        rc, out, _err = run_binary(info.path, key_bytes, timeout=30)
        if rc != 0 and extract_token(out) is None:
            raise RuntimeError("Recovered key did not produce a token")
        tok = extract_token(out)
        if tok is None:
            raise RuntimeError("Token not found in binary output")
        token = tok
    if token is None:
        token = ""
    return key_bytes, token


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Solve or run onion challenge binaries.",
    )
    ap.add_argument("--binary", type=pathlib.Path, default=pathlib.Path("another_onion"))
    ap.add_argument("--key", type=pathlib.Path, help="Run mode: key bytes path")
    ap.add_argument("--use-sample-key", action="store_true", help="Run mode: use ./a_key")
    ap.add_argument("--timeout", type=int, default=20, help="Run mode timeout")
    ap.add_argument("--show-output", action="store_true", help="Show program output in run mode")

    ap.add_argument("--recover", action="store_true", help="Recover key and token")
    ap.add_argument("--key-len", type=int, default=1024, help="Key length in bytes (default 1024)")
    ap.add_argument("--save-key", type=pathlib.Path, default=pathlib.Path("recovered_key.bin"))
    ap.add_argument("--max-stages", type=int, default=None, help="Debug: limit number of solved stages")
    ap.add_argument("--resume-key", type=pathlib.Path, help="Resume from a partially recovered key file")
    ap.add_argument("--resume-words", type=int, default=0, help="Number of 16-bit words already solved")
    ap.add_argument("--scan-workers", type=int, default=16, help="Worker count for stage scanner")
    ap.add_argument(
        "--scan-backend",
        choices=("process", "thread"),
        default="process",
        help="Parallel backend for stage scanner",
    )
    ap.add_argument(
        "--emulate-unsupported-sha-native",
        action="store_true",
        help="Handle unsupported SHA256RNDS2 in Unicorn by dispatching to a native helper.",
    )
    args = ap.parse_args()

    global EMULATE_UNSUPPORTED_SHA_NATIVE
    if args.emulate_unsupported_sha_native:
        EMULATE_UNSUPPORTED_SHA_NATIVE = True
        os.environ["ONION_SHA_NATIVE_EMU"] = "1"

    if args.use_sample_key and args.key is not None:
        print("Use either --key or --use-sample-key, not both.", file=sys.stderr)
        return 2

    if not args.binary.exists():
        print(f"Binary not found: {args.binary}", file=sys.stderr)
        return 2

    # Explicit run mode.
    if args.key is not None or args.use_sample_key:
        key_path = pathlib.Path("a_key") if args.use_sample_key else args.key
        if key_path is None or not key_path.exists():
            print(f"Key file not found: {key_path}", file=sys.stderr)
            return 2
        key_bytes = key_path.read_bytes()
        try:
            rc, out, err = run_binary(args.binary, key_bytes, args.timeout)
        except subprocess.TimeoutExpired:
            print("Execution timed out.", file=sys.stderr)
            return 3
        token = extract_token(out)
        if token:
            print(token)
            if args.show_output:
                print("\n=== program stdout ===")
                print(out, end="")
            return 0
        print(f"No token found. returncode={rc}", file=sys.stderr)
        if args.show_output:
            print("\n=== program stdout ===", file=sys.stderr)
            print(out, end="", file=sys.stderr)
            print("\n=== program stderr ===", file=sys.stderr)
            print(err, end="", file=sys.stderr)
        return 1

    # Default mode: recover.
    if not args.recover:
        # If no run-mode inputs were provided, auto-enable recovery.
        args.recover = True
    if args.recover:
        info = parse_binary_info(args.binary)
        known_words: list[int] = []
        if args.resume_words > 0:
            if args.resume_key is None:
                print("Provide --resume-key when using --resume-words.", file=sys.stderr)
                return 2
            if not args.resume_key.exists():
                print(f"Resume key file not found: {args.resume_key}", file=sys.stderr)
                return 2
            data = args.resume_key.read_bytes()
            needed = args.resume_words * 2
            if len(data) < needed:
                print(
                    f"Resume key file too short: have {len(data)} bytes, need at least {needed}.",
                    file=sys.stderr,
                )
                return 2
            known_words = [struct.unpack_from("<H", data, i * 2)[0] for i in range(args.resume_words)]

        print(
            f"[+] binary={args.binary} stage_entry={info.stage_entry:#x} read@plt={info.plt_read:#x}",
            flush=True,
        )
        if known_words:
            print(f"[+] resuming from {len(known_words)} known words", flush=True)
        key_bytes, token = recover_key_and_token(
            info=info,
            key_len=args.key_len,
            save_key_path=args.save_key,
            max_stages=args.max_stages,
            known_words=known_words,
            scan_workers=args.scan_workers,
            scan_backend=args.scan_backend,
        )
        print(f"[+] recovered key bytes: {len(key_bytes)}", flush=True)
        print(f"[+] key saved to: {args.save_key}", flush=True)
        if token:
            print(token)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
