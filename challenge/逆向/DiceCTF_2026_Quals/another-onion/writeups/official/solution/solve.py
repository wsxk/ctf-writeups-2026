#!/usr/bin/env python3
from __future__ import annotations

import argparse
import dataclasses
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOLVER_C = ROOT / "solve.c"
SOLVER_BIN = ROOT / "solve"
GENERATED_CONFIG = ROOT / "generated_config.h"


class SolveSetupError(RuntimeError):
    pass


@dataclasses.dataclass(frozen=True)
class LoadSegment:
    offset: int
    vaddr: int
    filesz: int
    memsz: int
    flags: str


@dataclasses.dataclass(frozen=True)
class SolverConfig:
    read_plt_addr: int
    mmap_plt_addr: int
    putchar_plt_addr: int
    target_start_code_addr: int
    nsegments: int
    code_seg: LoadSegment
    rodata_seg: LoadSegment
    data_seg: LoadSegment


@dataclasses.dataclass(frozen=True)
class DisasmInsn:
    addr: int
    mnemonic: str
    op_str: str


@dataclasses.dataclass(frozen=True)
class SectionInfo:
    name: str
    addr: int
    size: int


def run_checked(cmd: list[str], cwd: Path | None = None) -> str:
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SolveSetupError(
            f"Command failed ({' '.join(cmd)}):\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc.stdout


def run_checked_streaming(cmd: list[str], cwd: Path | None = None) -> None:
    proc = subprocess.Popen(cmd, cwd=cwd)
    ret = proc.wait()
    if ret != 0:
        raise SolveSetupError(f"Command failed ({' '.join(cmd)}), exit code {ret}")


def parse_entrypoint(binary: Path) -> int:
    out = run_checked(["readelf", "-W", "-h", str(binary)])
    match = re.search(r"Entry point address:\s*0x([0-9a-fA-F]+)", out)
    if match is None:
        raise SolveSetupError("Could not parse ELF entry point")
    return int(match.group(1), 16)


def parse_load_segments(binary: Path) -> list[LoadSegment]:
    out = run_checked(["readelf", "-W", "-l", str(binary)])
    segments: list[LoadSegment] = []
    for line in out.splitlines():
        parts = line.split()
        if not parts or parts[0] != "LOAD":
            continue
        if len(parts) < 8:
            continue
        offset = int(parts[1], 16)
        vaddr = int(parts[2], 16)
        filesz = int(parts[4], 16)
        memsz = int(parts[5], 16)
        flags = "".join(parts[6:-1])
        segments.append(
            LoadSegment(
                offset=offset,
                vaddr=vaddr,
                filesz=filesz,
                memsz=memsz,
                flags=flags,
            )
        )
    if not segments:
        raise SolveSetupError("No LOAD segments found in program headers")
    return segments


def parse_sections(binary: Path) -> list[SectionInfo]:
    out = run_checked(["readelf", "-W", "-S", str(binary)])
    sections: list[SectionInfo] = []
    for line in out.splitlines():
        # Example:
        # [16] .rodata PROGBITS 0000000000437000 037000 000110 ...
        match = re.match(
            r"^\s*\[\s*\d+\]\s+(\S+)\s+\S+\s+([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+([0-9a-fA-F]+)\s+",
            line,
        )
        if match is None:
            continue
        sections.append(
            SectionInfo(
                name=match.group(1),
                addr=int(match.group(2), 16),
                size=int(match.group(3), 16),
            )
        )
    return sections


def parse_plt_addr(binary: Path, symbol: str, *, required: bool = True) -> int:
    out = run_checked(["objdump", "-d", str(binary), "-M", "intel"])
    match = re.search(
        rf"^\s*([0-9a-fA-F]+)\s+<{re.escape(symbol)}@plt(?:\.sec)?>:",
        out,
        re.MULTILINE,
    )
    if match is None:
        if required:
            raise SolveSetupError(f"Could not find {symbol}@plt in objdump output")
        return 0
    return int(match.group(1), 16)


def disassemble_range(binary: Path, start: int, stop: int) -> list[DisasmInsn]:
    out = run_checked(
        [
            "objdump",
            "-d",
            str(binary),
            "-M",
            "intel",
            f"--start-address=0x{start:x}",
            f"--stop-address=0x{stop:x}",
        ]
    )
    insns: list[DisasmInsn] = []
    for line in out.splitlines():
        # Example:
        #  427d82: e8 01 87 fd ff        call   400488 <...>
        match = re.match(
            r"^\s*([0-9a-fA-F]+):\s+(?:[0-9a-fA-F]{2}(?:\s+[0-9a-fA-F]{2})*)\s+([a-z][a-z0-9]*)\s*(.*)$",
            line,
        )
        if match is None:
            continue
        addr = int(match.group(1), 16)
        mnemonic = match.group(2).strip()
        op_str = match.group(3).strip()
        insns.append(DisasmInsn(addr=addr, mnemonic=mnemonic, op_str=op_str))
    return insns


def parse_immediate_hex(op_str: str) -> int | None:
    first = op_str.strip().split(" ", 1)[0].rstrip(",")
    if first.startswith("0x"):
        return int(first, 16)
    if re.fullmatch(r"[0-9a-fA-F]+", first):
        return int(first, 16)
    return None


def parse_main_addr(binary: Path, entrypoint: int) -> int:
    insns = disassemble_range(binary, entrypoint, entrypoint + 0x120)
    for i in range(len(insns) - 1):
        insn = insns[i]
        if insn.mnemonic != "mov":
            continue
        match = re.fullmatch(r"rdi,0x([0-9a-fA-F]+)", insn.op_str.replace(" ", ""))
        if match is None:
            continue
        if insns[i + 1].mnemonic != "call":
            continue
        return int(match.group(1), 16)
    raise SolveSetupError("Could not locate main address from _start disassembly")


def parse_named_symbols(binary: Path) -> dict[str, int]:
    out = run_checked(["nm", "-n", str(binary)])
    symbols: dict[str, int] = {}
    for line in out.splitlines():
        match = re.match(r"^\s*([0-9a-fA-F]+)\s+\S\s+(\S+)$", line)
        if match is None:
            continue
        symbols[match.group(2)] = int(match.group(1), 16)
    return symbols


def infer_nsegments_from_symbols(symbols: dict[str, int]) -> int | None:
    seg_ids: list[int] = []
    for name in symbols:
        match = re.fullmatch(r"segment(\d+)", name)
        if match is None:
            continue
        seg_ids.append(int(match.group(1)))
    if not seg_ids:
        return None
    max_seg = max(seg_ids)
    if max_seg < 1:
        return None
    return max_seg - 1


def parse_main_metadata(binary: Path, main_addr: int) -> tuple[int, int]:
    insns = disassemble_range(binary, main_addr, main_addr + 0x200)
    if not insns:
        raise SolveSetupError("Failed to disassemble main")

    stack_alloc: int | None = None
    run_addr: int | None = None
    for i, insn in enumerate(insns):
        if stack_alloc is None and insn.mnemonic == "sub":
            match = re.fullmatch(r"rsp,0x([0-9a-fA-F]+)", insn.op_str.replace(" ", ""))
            if match is not None:
                stack_alloc = int(match.group(1), 16)
                continue
        if run_addr is None and insn.mnemonic == "call":
            imm = parse_immediate_hex(insn.op_str)
            if imm is None:
                continue
            # First direct call in generated main is run(NULL).
            run_addr = imm
            continue
        if stack_alloc is not None and run_addr is not None:
            break

    if stack_alloc is None:
        raise SolveSetupError("Could not infer addrs[] stack allocation from main")
    if run_addr is None:
        raise SolveSetupError("Could not infer run() address from main")
    if stack_alloc % 8 != 0:
        raise SolveSetupError(f"Unexpected stack allocation in main: 0x{stack_alloc:x}")

    nsegments = stack_alloc // 8 - 1
    if nsegments <= 0:
        raise SolveSetupError(f"Invalid inferred segment count: {nsegments}")
    return nsegments, run_addr


def parse_target_start(binary: Path, run_addr: int) -> int:
    insns = disassemble_range(binary, run_addr, run_addr + 0x80)
    for i in range(len(insns) - 2):
        i0, i1, i2 = insns[i], insns[i + 1], insns[i + 2]
        if i0.mnemonic == "test" and i0.op_str.replace(" ", "") == "rdi,rdi":
            if i1.mnemonic in ("je", "jz"):
                return i2.addr
    for insn in insns:
        if insn.mnemonic == "push" and insn.op_str.replace(" ", "") == "rbp":
            return insn.addr
    raise SolveSetupError("Could not infer run segment0 start address")


def select_segments(
    segments: list[LoadSegment], rodata_section: SectionInfo | None
) -> tuple[LoadSegment, LoadSegment, LoadSegment]:
    code = next((s for s in segments if "E" in s.flags), None)
    ro: LoadSegment | None = None
    if rodata_section is not None:
        rodata_end = rodata_section.addr + max(rodata_section.size, 1)
        containing = [
            s
            for s in segments
            if s.vaddr <= rodata_section.addr and rodata_end <= s.vaddr + s.memsz
        ]
        rwx_containing = [s for s in containing if "E" not in s.flags and "W" not in s.flags]
        if rwx_containing:
            ro = rwx_containing[0]
        elif containing:
            ro = containing[0]
    if ro is None:
        ro = next((s for s in segments if "E" not in s.flags and "W" not in s.flags), None)
    data = next((s for s in segments if "W" in s.flags), None)
    if code is None or ro is None or data is None:
        raise SolveSetupError(
            f"Could not identify code/rodata/data LOAD segments (found: {[s.flags for s in segments]})"
        )
    return code, ro, data


def analyze_binary(binary: Path) -> SolverConfig:
    segments = parse_load_segments(binary)
    sections = parse_sections(binary)
    rodata_section = next((s for s in sections if s.name == ".rodata"), None)
    code_seg, rodata_seg, data_seg = select_segments(segments, rodata_section)
    read_plt_addr = parse_plt_addr(binary, "read")
    mmap_plt_addr = parse_plt_addr(binary, "mmap", required=False)
    putchar_plt_addr = parse_plt_addr(binary, "putchar", required=False)
    if putchar_plt_addr == 0:
        putchar_plt_addr = parse_plt_addr(binary, "putc", required=False)
    if putchar_plt_addr == 0:
        raise SolveSetupError("Could not find putchar@plt or putc@plt in objdump output")
    symbols = parse_named_symbols(binary)

    run_addr = symbols.get("run")
    nsegments = infer_nsegments_from_symbols(symbols)
    if run_addr is not None and nsegments is not None:
        target_start_code_addr = run_addr
    else:
        entrypoint = parse_entrypoint(binary)
        main_addr = parse_main_addr(binary, entrypoint)
        nsegments, run_addr = parse_main_metadata(binary, main_addr)
        target_start_code_addr = parse_target_start(binary, run_addr)

    return SolverConfig(
        read_plt_addr=read_plt_addr,
        mmap_plt_addr=mmap_plt_addr,
        putchar_plt_addr=putchar_plt_addr,
        target_start_code_addr=target_start_code_addr,
        nsegments=nsegments,
        code_seg=code_seg,
        rodata_seg=rodata_seg,
        data_seg=data_seg,
    )


def write_generated_config(config: SolverConfig, config_path: Path) -> None:
    content = f"""// Auto-generated by solution/solve.py. Do not edit manually.
#pragma once

#define READ_PLT_ADDR_VALUE 0x{config.read_plt_addr:x}ULL
#define MMAP_PLT_ADDR_VALUE 0x{config.mmap_plt_addr:x}ULL
#define PUTCHAR_PLT_ADDR_VALUE 0x{config.putchar_plt_addr:x}ULL
#define TARGET_START_CODE_ADDR_VALUE 0x{config.target_start_code_addr:x}ULL
#define NSEGMENTS_VALUE {config.nsegments}

#define CODE_START_VALUE 0x{config.code_seg.vaddr:x}ULL
#define CODE_START_FILE_OFFSET_VALUE 0x{config.code_seg.offset:x}ULL
#define CODE_FILE_SIZE_VALUE 0x{config.code_seg.filesz:x}ULL
#define CODE_MEM_SIZE_VALUE 0x{config.code_seg.memsz:x}ULL

#define RODATA_START_VALUE 0x{config.rodata_seg.vaddr:x}ULL
#define RODATA_START_FILE_OFFSET_VALUE 0x{config.rodata_seg.offset:x}ULL
#define RODATA_FILE_SIZE_VALUE 0x{config.rodata_seg.filesz:x}ULL
#define RODATA_MEM_SIZE_VALUE 0x{config.rodata_seg.memsz:x}ULL

#define DATA_START_VALUE 0x{config.data_seg.vaddr:x}ULL
#define DATA_START_FILE_OFFSET_VALUE 0x{config.data_seg.offset:x}ULL
#define DATA_FILE_SIZE_VALUE 0x{config.data_seg.filesz:x}ULL
#define DATA_MEM_SIZE_VALUE 0x{config.data_seg.memsz:x}ULL
"""
    config_path.write_text(content)


def compile_solver() -> None:
    run_checked(
        [
            "clang",
            "-g",
            "-Wl,-Ttext-segment=0x8000000",
            "-o",
            str(SOLVER_BIN),
            str(SOLVER_C),
        ],
        cwd=ROOT,
    )


def run_solver(binary: Path, recovered: Path) -> None:
    run_checked_streaming([str(SOLVER_BIN), str(binary), str(recovered)], cwd=ROOT)


def extract_token(binary: Path, recovered: Path) -> str | None:
    recovered_bytes = recovered.read_bytes()
    proc = subprocess.run(
        [str(binary)],
        input=recovered_bytes,
        check=False,
        capture_output=True,
    )
    stdout = proc.stdout.decode("utf-8", errors="ignore")
    match = re.search(
        r"Congratulations!\s*Please submit the following token to get the flag:\s*([0-9a-fA-F]+)",
        stdout,
    )
    if match is None:
        return None
    return match.group(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Auto-configure, build, and run the native onion solver against a packed binary."
    )
    parser.add_argument(
        "binary",
        nargs="?",
        default="packed_real",
        help="Path to packed challenge binary (default: packed_real)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="recovered",
        help="Output path for recovered key bytes (default: recovered)",
    )
    parser.add_argument(
        "--build-only",
        action="store_true",
        help="Generate config and compile solver, but do not run it.",
    )
    parser.add_argument(
        "--segments",
        type=int,
        default=None,
        help="Override inferred segment count if auto-detection is off.",
    )
    parser.add_argument(
        "--extra-segments",
        type=int,
        default=0,
        help=(
            "Additional segments beyond inferred/overridden count. "
            "Must be 0 for this challenge layout."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    binary = Path(args.binary).resolve()
    recovered = Path(args.output).resolve()

    if not binary.exists():
        raise SolveSetupError(f"Binary does not exist: {binary}")

    config = analyze_binary(binary)
    if args.segments is not None:
        if args.segments <= 0:
            raise SolveSetupError("--segments must be positive")
        config = dataclasses.replace(config, nsegments=args.segments)
    if args.extra_segments < 0:
        raise SolveSetupError("--extra-segments must be >= 0")
    if args.extra_segments != 0:
        raise SolveSetupError(
            "--extra-segments must be 0: the final decoded segment has putchar calls "
            "and no read() calls, and is already handled by the built-in last-segment scoring."
        )

    write_generated_config(config, GENERATED_CONFIG)

    print(f"[+] Generated config: {GENERATED_CONFIG}")
    print(f"    read@plt               = 0x{config.read_plt_addr:x}")
    print(f"    mmap@plt               = 0x{config.mmap_plt_addr:x}")
    print(f"    putchar@plt            = 0x{config.putchar_plt_addr:x}")
    print(f"    segment0 start         = 0x{config.target_start_code_addr:x}")
    print(f"    inferred segment count = {config.nsegments}")

    compile_solver()
    print(f"[+] Compiled solver: {SOLVER_BIN}")

    if args.build_only:
        return 0

    run_solver(binary, recovered)
    print(f"[+] Recovered key written to: {recovered}")
    token = extract_token(binary, recovered)
    if token is not None:
        print(f"[+] Token: {token}")
    else:
        print("[!] Could not parse token from binary output using recovered key.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SolveSetupError as exc:
        print(f"[!] {exc}", file=sys.stderr)
        raise SystemExit(1)
