import os
import random
import sys
from dataclasses import dataclass

POOL_SMALL_SIZE = 1 << 16
POOL_SMALL_ADDR_MASK = POOL_SMALL_SIZE - 1
POOL_LARGE_SIZE = 1 << 24
POOL_LARGE_ADDR_MASK = POOL_LARGE_SIZE - 1
STREAM_BUFFER_ADDR = 0x90000000
STREAM_BUFFER_SIZE = 0x01000000
MMAP_PROT_RW = 0x3
MMAP_FLAGS_FIXED_PRIVATE_ANON = 0x32


def parse_env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw, 0)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer (got {raw!r})") from exc


def parse_env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"{name} must be a boolean-like value (got {raw!r})")


POOL_HASH_BYTES = parse_env_int("POOL_HASH_BYTES", POOL_SMALL_SIZE)
if POOL_HASH_BYTES <= 0:
    raise RuntimeError("POOL_HASH_BYTES must be positive")
if POOL_HASH_BYTES > POOL_SMALL_SIZE:
    raise RuntimeError(
        f"POOL_HASH_BYTES ({POOL_HASH_BYTES}) cannot exceed POOL_SMALL_SIZE ({POOL_SMALL_SIZE})"
    )
if POOL_HASH_BYTES % 16 != 0:
    raise RuntimeError("POOL_HASH_BYTES must be divisible by 16")
POOL_HASH_CHUNKS = POOL_HASH_BYTES // 16

PERM_OP_ADD = 0
PERM_OP_ROL = 1
PERM_OP_MUL = 2
PERM_OP_XOR = 3
PERM_OP_MAX = 7
PERM_LARGE_XOR_COUNT = 10


class CodeWriter:
    def __init__(self, indent_unit: str = "    "):
        self.code: list[str] = []
        self._indent = 0
        self._indent_unit = indent_unit

    def write(self, text: str = ""):
        for line in text.split("\n"):
            if line:
                self.code.append(self._indent_unit * self._indent + line)
            else:
                self.code.append("")

    def indent(self):
        self._indent += 1

    def dedent(self):
        self._indent -= 1
        if self._indent < 0:
            raise RuntimeError("negative indentation")

    def save(self, path: str):
        with open(path, "w") as f:
            for line in self.code:
                f.write(line + "\n")


@dataclass(frozen=True)
class StageSpec:
    kind: str  # "sha" | "perm" | "pool_mutation"
    rounds: int = 0
    idx0: int = 0
    idx1: int = 0
    rot: int = 1
    xor_const: int = 0
    mix_const: int = 0
    pool_len: int = 0
    pool_kind: int = 0  # 0=small, 1=large
    perm_ops: tuple[tuple[int, int, tuple[int, ...]], ...] = tuple()


@dataclass(frozen=True)
class TargetCipherSpec:
    target_index: int
    prefix_passes: tuple[tuple[StageSpec, ...], ...]
    final_pass: tuple[StageSpec, ...]


@dataclass(frozen=True)
class SegmentSpec:
    targets: tuple[TargetCipherSpec, ...]


@dataclass(frozen=True)
class DummyLocalSpec:
    c_type: str
    count: int
    align: int
    idx0: int
    idx1: int
    init_const: int
    mix_const: int


SHA_LOOP_LABEL_COUNTER = 0
KEYSCHED_LABEL_COUNTER = 0
TARGET_LOOP_LABEL_COUNTER = 0
POOL_MUT_LABEL_COUNTER = 0
STREAM_PASS_LABEL_COUNTER = 0
PERM_STAGE_PROB = 0.3
POOL_MUTATION_STAGE_PROB = 0.3
SHA_ROUNDS_MIN = 20
SHA_ROUNDS_MAX = 30
STREAM_LOOP_COUNT_MIN = 2
STREAM_LOOP_COUNT_MAX = 4
STREAM_PREFIX_LEN = 128
ENABLE_DUMMY_LOCALS = parse_env_bool("ENABLE_DUMMY_LOCALS", True)
DUMMY_LOCAL_TYPE_SPECS = (
    ("uint8_t", 17, 61),
    ("uint16_t", 9, 29),
    ("uint32_t", 5, 17),
    ("uint64_t", 3, 11),
)


def random_sha_stage() -> StageSpec:
    return StageSpec(
        kind="sha",
        rounds=random.randint(SHA_ROUNDS_MIN, SHA_ROUNDS_MAX),
        idx0=random.randint(0, 3),
        idx1=random.randint(0, 3),
        rot=random.randint(1, 31),
        xor_const=random.getrandbits(32),
        mix_const=random.getrandbits(32),
    )


def random_perm_stage() -> StageSpec:
    nops = random.randint(5, 7)
    ops: list[tuple[int, int, tuple[int, ...]]] = []
    for _ in range(nops):
        kind = random.choice((PERM_OP_ADD, PERM_OP_ROL, PERM_OP_MUL, PERM_OP_XOR))
        large_addrs = tuple(random.sample(range(POOL_LARGE_SIZE), PERM_LARGE_XOR_COUNT))
        ops.append((kind, random.getrandbits(16), large_addrs))
    return StageSpec(
        kind="perm",
        perm_ops=tuple(ops),
    )


def random_pool_mutation_stage() -> StageSpec:
    return StageSpec(
        kind="pool_mutation",
        pool_len=random.randint(2048, 4096),
        pool_kind=random.randint(0, 1),
    )


def random_pass_stages(require_pool: bool) -> tuple[StageSpec, ...]:
    nstages = random.randint(3, 4)
    stages: list[StageSpec] = []
    for _ in range(nstages):
        r = random.random()
        if not require_pool and r >= PERM_STAGE_PROB:
            stages.append(random_sha_stage())
        elif r < PERM_STAGE_PROB:
            stages.append(random_perm_stage())
        elif r < PERM_STAGE_PROB + POOL_MUTATION_STAGE_PROB:
            stages.append(random_pool_mutation_stage())
        else:
            stages.append(random_sha_stage())

    sha_idxs = [i for i, stage in enumerate(stages) if stage.kind == "sha"]
    pool_idxs = [i for i, stage in enumerate(stages) if stage.kind == "pool_mutation"]

    if require_pool and not sha_idxs and not pool_idxs:
        i_sha, i_pool = random.sample(range(len(stages)), 2)
        stages[i_sha] = random_sha_stage()
        stages[i_pool] = random_pool_mutation_stage()
    elif not sha_idxs:
        pool_set = set(pool_idxs)
        candidates = [i for i in range(len(stages)) if i not in pool_set]
        i_sha = random.choice(candidates if candidates else list(range(len(stages))))
        stages[i_sha] = random_sha_stage()
    elif require_pool and not pool_idxs:
        sha_set = set(sha_idxs)
        candidates = [i for i in range(len(stages)) if i not in sha_set]
        i_pool = random.choice(candidates if candidates else list(range(len(stages))))
        stages[i_pool] = random_pool_mutation_stage()
    elif not require_pool:
        stages = [stage for stage in stages if stage.kind != "pool_mutation"]
        if not stages:
            stages.append(random_sha_stage())
        if not any(stage.kind == "sha" for stage in stages):
            stages[random.randrange(len(stages))] = random_sha_stage()

    return tuple(stages)


def random_target_cipher(target_index: int) -> TargetCipherSpec:
    loop_count = random.randint(STREAM_LOOP_COUNT_MIN, STREAM_LOOP_COUNT_MAX)
    prefix_passes = tuple(
        random_pass_stages(require_pool=(pass_idx + 1 != loop_count))
        for pass_idx in range(loop_count)
    )
    final_pass: tuple[StageSpec, ...] = tuple()

    return TargetCipherSpec(
        target_index=target_index,
        prefix_passes=prefix_passes,
        final_pass=final_pass,
    )


def make_segment_specs(nsegments: int) -> list[SegmentSpec]:
    specs: list[SegmentSpec] = []
    for seg in range(nsegments):
        target_specs = [random_target_cipher(seg + 1)]
        specs.append(SegmentSpec(targets=tuple(target_specs)))
    return specs


def random_sha_init_bytes() -> list[int]:
    out = [random.getrandbits(8) for _ in range(16)]
    if all(v == 0 for v in out):
        out[0] = 1
    return out


def random_dummy_local_spec() -> DummyLocalSpec:
    c_type, min_count, max_count = random.choice(DUMMY_LOCAL_TYPE_SPECS)
    count = random.randint(min_count, max_count)
    return DummyLocalSpec(
        c_type=c_type,
        count=count,
        align=random.choice((8, 16, 32, 64)),
        idx0=random.randrange(count),
        idx1=random.randrange(count),
        init_const=random.getrandbits(32),
        mix_const=random.getrandbits(32),
    )


def random_segment_dummy_locals() -> tuple[DummyLocalSpec, ...]:
    if not ENABLE_DUMMY_LOCALS:
        return tuple()
    return tuple(random_dummy_local_spec() for _ in range(random.randint(2, 5)))


def emit_perm_stage_asm(asm: CodeWriter, stage: StageSpec):
    for kind, c in stage.perm_ops:
        if kind == PERM_OP_ADD:
            asm.write(f"add eax, 0x{c:08x}")
        elif kind == PERM_OP_ROL:
            asm.write(f"rol eax, {c}")
        elif kind == PERM_OP_MUL:
            asm.write(f"imul eax, eax, 0x{c:08x}")
        elif kind == PERM_OP_XOR:
            asm.write(f"xor eax, 0x{c:08x}")
        else:
            raise RuntimeError(f"unsupported perm op kind: {kind}")


def emit_sha_stage_asm(asm: CodeWriter, stage: StageSpec):
    global SHA_LOOP_LABEL_COUNTER
    loop_id = SHA_LOOP_LABEL_COUNTER
    SHA_LOOP_LABEL_COUNTER += 1

    asm.write("movd xmm0, eax")
    asm.write("pshufd xmm0, xmm0, 0x00")
    asm.write(f"mov ecx, 0x{stage.mix_const:08x}")
    asm.write("movd xmm3, ecx")
    asm.write("pshufd xmm3, xmm3, 0x00")
    asm.write("pxor xmm0, xmm3")
    asm.write("movdqa xmm1, xmmword ptr [rip + sha_s0]")
    asm.write("movdqa xmm2, xmmword ptr [rip + sha_s1]")
    asm.write(f"mov ecx, {stage.rounds}")
    asm.write(f".Lsha_round_loop_{loop_id}:")
    asm.write("sha256rnds2 xmm1, xmm2, xmm0")
    asm.write("pshufd xmm0, xmm0, 0x0e")
    asm.write("sha256rnds2 xmm2, xmm1, xmm0")
    asm.write("dec ecx")
    asm.write(f"jne .Lsha_round_loop_{loop_id}")
    asm.write("movdqa xmmword ptr [rip + sha_s0], xmm1")
    asm.write("movdqa xmmword ptr [rip + sha_s1], xmm2")
    asm.write(f"pextrd eax, xmm1, {stage.idx0}")
    asm.write(f"pextrd ebx, xmm2, {stage.idx1}")
    asm.write("xor eax, ebx")
    asm.write(f"rol eax, {stage.rot}")
    asm.write(f"xor eax, 0x{stage.xor_const:08x}")


def emit_pool_mutation_stage_asm(asm: CodeWriter, stage: StageSpec):
    global POOL_MUT_LABEL_COUNTER
    label_id = POOL_MUT_LABEL_COUNTER
    POOL_MUT_LABEL_COUNTER += 1

    asm.write("mov ecx, eax")
    asm.write(f"and ecx, 0x{POOL_ADDR_MASK:08x}")
    asm.write(f"cmp ecx, 0x{POOL_SIZE - 4096:08x}")
    asm.write(f"jb .Lpool_mut_noadj_{label_id}")
    asm.write("sub ecx, 4096")
    asm.write(f".Lpool_mut_noadj_{label_id}:")
    asm.write("push rax")
    asm.write("lea rdi, [rip + pool]")
    asm.write("add rdi, rcx")
    asm.write("mov dl, byte ptr [rdi]")
    asm.write("mov eax, dword ptr [rsp]")
    asm.write("shr eax, 24")
    asm.write("xor al, dl")
    asm.write(f"mov ecx, {stage.pool_len}")
    asm.write("rep stosb")
    asm.write("pop rax")


def emit_stage_asm(asm: CodeWriter, stage: StageSpec):
    if stage.kind == "sha":
        emit_sha_stage_asm(asm, stage)
    elif stage.kind == "perm":
        emit_perm_stage_asm(asm, stage)
    elif stage.kind == "pool_mutation":
        return
    else:
        raise RuntimeError(f"unsupported stage kind: {stage.kind}")


def emit_interloop_pool_mutation_asm(asm: CodeWriter, target: TargetCipherSpec):
    pool_stages = [stage for stage in target.stages if stage.kind == "pool_mutation"]
    if not pool_stages:
        return
    asm.write("mov eax, dword ptr [rip + state_x]")
    for stage in pool_stages:
        emit_pool_mutation_stage_asm(asm, stage)
    asm.write("mov dword ptr [rip + state_x], eax")


def emit_stream_pass_asm(
    asm: CodeWriter,
    seg: int,
    target_idx: int,
    pass_idx: int,
    target: TargetCipherSpec,
    assign_tail: bool,
):
    global TARGET_LOOP_LABEL_COUNTER, STREAM_PASS_LABEL_COUNTER
    loop_id = TARGET_LOOP_LABEL_COUNTER
    TARGET_LOOP_LABEL_COUNTER += 1
    label_id = STREAM_PASS_LABEL_COUNTER
    STREAM_PASS_LABEL_COUNTER += 1

    asm.write(f"lea r8, [rip + segment{target.target_index}]")
    asm.write(f"lea r9, [rip + segment{target.target_index + 1}]")
    asm.write("sub r9, r8")
    if assign_tail:
        asm.write("mov r11, r9")
        asm.write(f"cmp r11, {STREAM_PREFIX_LEN}")
        asm.write(f"jae .Ltarget_span_ready_{seg}_{target_idx}_{pass_idx}_{label_id}")
        asm.write(f"mov r11d, {STREAM_PREFIX_LEN}")
        asm.write(f".Ltarget_span_ready_{seg}_{target_idx}_{pass_idx}_{label_id}:")
    else:
        asm.write(f"mov r11d, {STREAM_PREFIX_LEN}")
    asm.write("xor r10d, r10d")
    asm.write("mov r13, r12")
    asm.write(f".Ltarget_stream_pass_{seg}_{target_idx}_{pass_idx}_{loop_id}:")
    asm.write("cmp r10, r11")
    asm.write(f"jae .Ltarget_stream_pass_done_{seg}_{target_idx}_{pass_idx}_{loop_id}")
    asm.write("mov eax, dword ptr [rip + state_x]")
    for stage in target.stages:
        emit_stage_asm(asm, stage)
    asm.write("mov dword ptr [rip + state_x], eax")
    if assign_tail:
        asm.write(f"cmp r10, {STREAM_PREFIX_LEN}")
        asm.write(f"jae .Ltarget_stream_assign_{seg}_{target_idx}_{pass_idx}_{label_id}")
    asm.write("xor byte ptr [r13 + r10], al")
    if assign_tail:
        asm.write(f"jmp .Ltarget_stream_store_done_{seg}_{target_idx}_{pass_idx}_{label_id}")
        asm.write(f".Ltarget_stream_assign_{seg}_{target_idx}_{pass_idx}_{label_id}:")
        asm.write("mov byte ptr [r13 + r10], al")
        asm.write(f".Ltarget_stream_store_done_{seg}_{target_idx}_{pass_idx}_{label_id}:")
    asm.write("inc r10")
    asm.write(f"jmp .Ltarget_stream_pass_{seg}_{target_idx}_{pass_idx}_{loop_id}")
    asm.write(f".Ltarget_stream_pass_done_{seg}_{target_idx}_{pass_idx}_{loop_id}:")


def emit_keyschedule_asm(asm: CodeWriter, seg: int):
    global KEYSCHED_LABEL_COUNTER
    loop_id = KEYSCHED_LABEL_COUNTER
    KEYSCHED_LABEL_COUNTER += 1

    asm.write("lea r12, [rip + pool]")
    asm.write(f"mov ecx, {POOL_HASH_CHUNKS}")
    asm.write("movdqa xmm1, xmmword ptr [rip + sha_s0]")
    asm.write("movdqa xmm2, xmmword ptr [rip + sha_s1]")
    asm.write(f".Lkeysched_loop_{seg}_{loop_id}:")
    asm.write("movdqu xmm0, xmmword ptr [r12]")
    asm.write("sha256rnds2 xmm1, xmm2, xmm0")
    asm.write("pshufd xmm0, xmm0, 0x0e")
    asm.write("sha256rnds2 xmm2, xmm1, xmm0")
    asm.write("add r12, 16")
    asm.write("dec ecx")
    asm.write(f"jne .Lkeysched_loop_{seg}_{loop_id}")
    asm.write("movdqa xmmword ptr [rip + sha_s0], xmm1")
    asm.write("movdqa xmmword ptr [rip + sha_s1], xmm2")


def emit_segment_asm(asm: CodeWriter, seg: int, spec: SegmentSpec):
    global TARGET_LOOP_LABEL_COUNTER
    asm.write(f".globl segment{seg}")
    asm.write(f"segment{seg}:")
    asm.indent()

    if seg == 0:
        asm.write("cld")

    # 1) key scheduling phase: fold full pool into SHA scratch before reads
    emit_keyschedule_asm(asm, seg)

    # 2) read two bytes into x16, then replicate to x32: x | (x << 16)
    asm.write("mov edi, 0")
    asm.write("lea rsi, [rip + input_buf]")
    asm.write("mov edx, 1")
    asm.write("call read@PLT")
    asm.write("movzx eax, byte ptr [rip + input_buf]")
    asm.write("mov dword ptr [rip + state_x], eax")

    asm.write("mov edi, 0")
    asm.write("lea rsi, [rip + input_buf]")
    asm.write("mov edx, 1")
    asm.write("call read@PLT")
    asm.write("movzx eax, byte ptr [rip + input_buf]")
    asm.write("shl eax, 8")
    asm.write("mov edx, dword ptr [rip + state_x]")
    asm.write("or eax, edx")
    asm.write("mov edx, eax")
    asm.write("shl edx, 16")
    asm.write("or eax, edx")
    asm.write("mov dword ptr [rip + state_x], eax")

    # 3) generate the next-segment keystream into the mmap scratch buffer
    asm.write("mov r12, qword ptr [rip + stream_buf_ptr]")
    for target_idx, target in enumerate(spec.targets):
        asm.write("mov r13, r12")
        asm.write("xor eax, eax")
        asm.write("mov rdi, r13")
        asm.write(f"mov ecx, {STREAM_PREFIX_LEN}")
        asm.write("rep stosb")
        for pass_idx in range(target.loop_count):
            emit_stream_pass_asm(
                asm,
                seg,
                target_idx,
                pass_idx,
                target,
                assign_tail=(pass_idx + 1 == target.loop_count),
            )
            if pass_idx + 1 != target.loop_count:
                emit_interloop_pool_mutation_asm(asm, target)

    # 4) xor the next segment from the buffered keystream
    asm.write("mov r12, qword ptr [rip + stream_buf_ptr]")
    for target_idx, target in enumerate(spec.targets):
        loop_id = TARGET_LOOP_LABEL_COUNTER
        TARGET_LOOP_LABEL_COUNTER += 1
        asm.write(f"lea r8, [rip + segment{target.target_index}]")
        asm.write(f"lea r9, [rip + segment{target.target_index + 1}]")
        asm.write("sub r9, r8")
        asm.write("xor r10d, r10d")
        asm.write("mov r13, r12")
        asm.write(f".Ltarget_xor_loop_{seg}_{target_idx}_{loop_id}:")
        asm.write("cmp r10, r9")
        asm.write(f"jae .Ltarget_xor_done_{seg}_{target_idx}_{loop_id}")
        asm.write("mov al, byte ptr [r13 + r10]")
        asm.write("xor byte ptr [r8 + r10], al")
        asm.write("inc r10")
        asm.write(f"jmp .Ltarget_xor_loop_{seg}_{target_idx}_{loop_id}")
        asm.write(f".Ltarget_xor_done_{seg}_{target_idx}_{loop_id}:")

    asm.dedent()


def emit_run_asm(asm: CodeWriter, specs: list[SegmentSpec], flag: str):
    nsegments = len(specs)

    asm.write(".text")
    asm.write(".intel_syntax noprefix")
    asm.write(".globl run")
    asm.write(".type run,@function")
    asm.write("run:")
    asm.indent()
    asm.write("test rdi, rdi")
    asm.write("je .Lrun_return_end")
    asm.write("mov qword ptr [rip + addrs_saved], rdi")
    asm.write(f"mov edi, 0x{STREAM_BUFFER_ADDR:08x}")
    asm.write(f"mov esi, 0x{STREAM_BUFFER_SIZE:08x}")
    asm.write(f"mov edx, 0x{MMAP_PROT_RW:x}")
    asm.write(f"mov ecx, 0x{MMAP_FLAGS_FIXED_PRIVATE_ANON:x}")
    asm.write("mov r8d, -1")
    asm.write("xor r9d, r9d")
    asm.write("sub rsp, 8")
    asm.write("call mmap@PLT")
    asm.write("add rsp, 8")
    asm.write("mov qword ptr [rip + stream_buf_ptr], rax")
    asm.write("movdqa xmm0, xmmword ptr [rip + sha_init0]")
    asm.write("movdqa xmmword ptr [rip + sha_s0], xmm0")
    asm.write("movdqa xmm0, xmmword ptr [rip + sha_init1]")
    asm.write("movdqa xmmword ptr [rip + sha_s1], xmm0")
    asm.dedent()

    for seg, spec in enumerate(specs):
        emit_segment_asm(asm, seg, spec)

    asm.write("addresses:")
    asm.indent()
    asm.write("mov rax, qword ptr [rip + addrs_saved]")
    for i in range(nsegments + 1):
        asm.write(f"lea rcx, [rip + segment{i}]")
        asm.write(f"mov qword ptr [rax + {i * 8}], rcx")
    asm.dedent()

    asm.write(f".globl segment{nsegments}")
    asm.write(f"segment{nsegments}:")
    asm.indent()
    message = (
        "Congratulations! Please submit the following token to get the flag: "
        f"{flag}"
    )
    for ch in message:
        asm.write(f"mov edi, {ord(ch)}")
        asm.write("call putchar@PLT")
    asm.dedent()

    asm.write(f".globl segment{nsegments + 1}")
    asm.write(f"segment{nsegments + 1}:")
    asm.indent()
    asm.write("xor eax, eax")
    asm.write("ret")
    asm.dedent()

    asm.write(".Lrun_return_end:")
    asm.indent()
    asm.write(f"lea rax, [rip + segment{nsegments + 1}]")
    asm.write("ret")
    asm.dedent()
    asm.write(".size run, .-run")


def emit_main_asm(asm: CodeWriter, nsegments: int):
    stack_alloc = (nsegments + 1) * 8
    need_align_fix = (nsegments % 2) == 1

    asm.write(".globl main")
    asm.write(".type main,@function")
    asm.write("main:")
    asm.indent()
    asm.write(f"sub rsp, {stack_alloc}")

    if need_align_fix:
        asm.write("sub rsp, 8")
    asm.write("xor edi, edi")
    asm.write("call run")
    if need_align_fix:
        asm.write("add rsp, 8")

    asm.write("mov r8, rax")
    asm.write("lea rax, [rip + run]")
    asm.write("mov rcx, rax")
    asm.write("and rcx, -4096")
    asm.write("lea rdx, [r8 + 4095]")
    asm.write("and rdx, -4096")
    asm.write("sub rdx, rcx")
    asm.write("mov rdi, rcx")
    asm.write("mov rsi, rdx")
    asm.write("mov edx, 7")
    if need_align_fix:
        asm.write("sub rsp, 8")
    asm.write("call mprotect@PLT")
    if need_align_fix:
        asm.write("add rsp, 8")

    if need_align_fix:
        asm.write("sub rsp, 8")
        asm.write("lea rdi, [rsp + 8]")
    else:
        asm.write("lea rdi, [rsp]")
    asm.write("call run")
    if need_align_fix:
        asm.write("add rsp, 8")

    asm.write(f"add rsp, {stack_alloc}")
    asm.write("xor eax, eax")
    asm.write("ret")
    asm.dedent()
    asm.write(".size main, .-main")


def emit_data_asm(asm: CodeWriter, sha_init0: list[int], sha_init1: list[int]):
    asm.write(".section .data")
    asm.write(".align 16")
    asm.write("sha_init0:")
    asm.write(".byte " + ", ".join(f"0x{x:02x}" for x in sha_init0))
    asm.write("sha_init1:")
    asm.write(".byte " + ", ".join(f"0x{x:02x}" for x in sha_init1))

    asm.write(".section .bss")
    asm.write(".align 16")
    asm.write("sha_s0:")
    asm.write(".zero 16")
    asm.write("sha_s1:")
    asm.write(".zero 16")
    asm.write("state_x:")
    asm.write(".zero 4")
    asm.write("input_buf:")
    asm.write(".zero 1")
    asm.write(".align 8")
    asm.write("addrs_saved:")
    asm.write(".zero 8")
    asm.write("stream_buf_ptr:")
    asm.write(".zero 8")
    asm.write(".align 64")
    asm.write("pool:")
    asm.write(f".zero {POOL_SIZE}")


def flatten_specs_for_encryptor(
    specs: list[SegmentSpec],
) -> tuple[
    list[tuple[int, int]],
    list[tuple[int, int, int, int, int]],
    list[tuple[int, int]],
    list[StageSpec],
]:
    segment_rows: list[tuple[int, int]] = []
    target_rows: list[tuple[int, int, int, int, int]] = []
    pass_rows: list[tuple[int, int]] = []
    stage_rows: list[StageSpec] = []

    for seg in specs:
        target_offset = len(target_rows)
        for target in seg.targets:
            prefix_pass_offset = len(pass_rows)
            for pass_stages in target.prefix_passes:
                stage_offset = len(stage_rows)
                stage_rows.extend(pass_stages)
                pass_rows.append((stage_offset, len(pass_stages)))
            final_stage_offset = len(stage_rows)
            stage_rows.extend(target.final_pass)
            target_rows.append(
                (
                    target.target_index,
                    prefix_pass_offset,
                    len(target.prefix_passes),
                    final_stage_offset,
                    len(target.final_pass),
                )
            )
        segment_rows.append((target_offset, len(seg.targets)))

    return segment_rows, target_rows, pass_rows, stage_rows


def emit_stage_initializer(stage: StageSpec) -> str:
    zero_kinds = ", ".join("0" for _ in range(PERM_OP_MAX))
    zero_small_addrs = ", ".join("0u" for _ in range(PERM_OP_MAX))
    zero_large_rows = ", ".join(
        "{"
        + ", ".join("0u" for _ in range(PERM_LARGE_XOR_COUNT))
        + "}"
        for _ in range(PERM_OP_MAX)
    )
    if stage.kind == "sha":
        return (
            "{"
            f"0, {stage.rounds}, {stage.idx0}, {stage.idx1}, {stage.rot}, "
            f"0x{stage.xor_const:08x}u, 0x{stage.mix_const:08x}u, 0, 0, 0, "
            "{" + zero_kinds + "}, {" + zero_small_addrs + "}, {"
            + zero_large_rows
            + "}"
            "}"
        )
    if stage.kind == "perm":
        kinds = [str(kind) for kind, _, _ in stage.perm_ops]
        small_addrs = [f"0x{small_addr:04x}u" for _, small_addr, _ in stage.perm_ops]
        large_addr_rows = [
            "{"
            + ", ".join(f"0x{large_addr:06x}u" for large_addr in large_addrs)
            + "}"
            for _, _, large_addrs in stage.perm_ops
        ]
        while len(kinds) < PERM_OP_MAX:
            kinds.append("0")
            small_addrs.append("0u")
            large_addr_rows.append(
                "{"
                + ", ".join("0u" for _ in range(PERM_LARGE_XOR_COUNT))
                + "}"
            )
        return (
            "{"
            f"1, 0, 0, 0, 0, 0x00000000u, 0x00000000u, 0, 0, {len(stage.perm_ops)}, "
            "{"
            + ", ".join(kinds)
            + "}, {"
            + ", ".join(small_addrs)
            + "}, {"
            + ", ".join(large_addr_rows)
            + "}"
            "}"
        )
    if stage.kind == "pool_mutation":
        return (
            "{"
            f"2, 0, 0, 0, 0, 0x00000000u, 0x00000000u, {stage.pool_len}, {stage.pool_kind}, 0, "
            "{"
            + zero_kinds
            + "}, {"
            + zero_small_addrs
            + "}, {"
            + zero_large_rows
            + "}"
            "}"
        )
    raise RuntimeError(f"unsupported stage kind: {stage.kind}")


def emit_encryptor_c(
    c: CodeWriter,
    pack_name: str,
    nsegments: int,
    sha_init0: list[int],
    sha_init1: list[int],
    specs: list[SegmentSpec],
):
    seg_rows, target_rows, pass_rows, stage_rows = flatten_specs_for_encryptor(specs)

    c.write("#include <immintrin.h>")
    c.write("#include <stdint.h>")
    c.write("#include <stdio.h>")
    c.write("#include <stdlib.h>")
    c.write("#include <string.h>")
    c.write("#include <limits.h>")
    c.write("")
    c.write(f"#define PACK_NAME \"{pack_name}\"")
    c.write(f"#define NSEGMENTS {nsegments}")
    c.write(f"#define POOL_SMALL_SIZE {POOL_SMALL_SIZE}u")
    c.write(f"#define POOL_LARGE_SIZE {POOL_LARGE_SIZE}u")
    c.write(f"#define POOL_HASH_BYTES {POOL_HASH_BYTES}u")
    c.write(f"#define STREAM_BUFFER_SIZE {STREAM_BUFFER_SIZE}u")
    c.write(f"#define STREAM_PREFIX_LEN {STREAM_PREFIX_LEN}u")
    c.write(f"#define POOL_SMALL_ADDR_MASK 0x{POOL_SMALL_ADDR_MASK:08x}u")
    c.write(f"#define POOL_LARGE_ADDR_MASK 0x{POOL_LARGE_ADDR_MASK:08x}u")
    c.write(f"#define PERM_OP_MAX {PERM_OP_MAX}u")
    c.write(f"#define PERM_LARGE_XOR_COUNT {PERM_LARGE_XOR_COUNT}u")
    c.write("")

    c.write("typedef struct {")
    c.indent()
    c.write("uint8_t kind;")
    c.write("uint8_t rounds;")
    c.write("uint8_t idx0;")
    c.write("uint8_t idx1;")
    c.write("uint8_t rot;")
    c.write("uint32_t xor_const;")
    c.write("uint32_t mix_const;")
    c.write("uint16_t pool_len;")
    c.write("uint8_t pool_kind;")
    c.write("uint8_t op_count;")
    c.write("uint8_t op_kind[PERM_OP_MAX];")
    c.write("uint32_t op_small_addr[PERM_OP_MAX];")
    c.write("uint32_t op_large_addr[PERM_OP_MAX][PERM_LARGE_XOR_COUNT];")
    c.dedent()
    c.write("} StageSpec;")
    c.write("")

    c.write("typedef struct {")
    c.indent()
    c.write("uint32_t stage_offset;")
    c.write("uint16_t stage_count;")
    c.dedent()
    c.write("} PassSpec;")
    c.write("")

    c.write("typedef struct {")
    c.indent()
    c.write("uint16_t target_index;")
    c.write("uint16_t prefix_pass_offset;")
    c.write("uint8_t prefix_pass_count;")
    c.write("uint32_t final_stage_offset;")
    c.write("uint16_t final_stage_count;")
    c.dedent()
    c.write("} TargetSpec;")
    c.write("")

    c.write("typedef struct {")
    c.indent()
    c.write("uint32_t target_offset;")
    c.write("uint16_t target_count;")
    c.dedent()
    c.write("} SegmentSpec;")
    c.write("")

    c.write("typedef struct {")
    c.indent()
    c.write("uint64_t vstart;")
    c.write("uint64_t vend;")
    c.write("uint64_t file_off;")
    c.dedent()
    c.write("} LoadSeg;")
    c.write("")

    c.write("static const uint8_t SHA_INIT0[16] = {")
    c.indent()
    c.write(", ".join(f"0x{x:02x}" for x in sha_init0))
    c.dedent()
    c.write("};")
    c.write("static const uint8_t SHA_INIT1[16] = {")
    c.indent()
    c.write(", ".join(f"0x{x:02x}" for x in sha_init1))
    c.dedent()
    c.write("};")
    c.write("")

    c.write(f"static const SegmentSpec SEGMENT_SPECS[{len(seg_rows)}] = {{")
    c.indent()
    for row in seg_rows:
        c.write(f"{{{row[0]}, {row[1]}}},")
    c.dedent()
    c.write("};")
    c.write("")

    c.write(f"static const TargetSpec TARGET_SPECS[{len(target_rows)}] = {{")
    c.indent()
    for row in target_rows:
        c.write(f"{{{row[0]}, {row[1]}, {row[2]}, {row[3]}, {row[4]}}},")
    c.dedent()
    c.write("};")
    c.write("")

    c.write(f"static const PassSpec PASS_SPECS[{len(pass_rows)}] = {{")
    c.indent()
    for row in pass_rows:
        c.write(f"{{{row[0]}, {row[1]}}},")
    c.dedent()
    c.write("};")
    c.write("")

    c.write(f"static const StageSpec STAGE_SPECS[{len(stage_rows)}] = {{")
    c.indent()
    for stage in stage_rows:
        c.write(emit_stage_initializer(stage) + ",")
    c.dedent()
    c.write("};")
    c.write("")

    c.write("static uint8_t pool_small[POOL_SMALL_SIZE];")
    c.write("static uint8_t pool_large[POOL_LARGE_SIZE];")
    c.write("static uint8_t stream_buf[STREAM_BUFFER_SIZE];")
    c.write("static __m128i sha_s0;")
    c.write("static __m128i sha_s1;")
    c.write("")

    c.write("static inline uint32_t rol32(uint32_t x, unsigned r) {")
    c.indent()
    c.write("r &= 31u;")
    c.write("if (r == 0) return x;")
    c.write("return (x << r) | (x >> (32u - r));")
    c.dedent()
    c.write("}")
    c.write("")

    c.write("static void init_sha_state(void) {")
    c.indent()
    c.write("sha_s0 = _mm_loadu_si128((const __m128i *)SHA_INIT0);")
    c.write("sha_s1 = _mm_loadu_si128((const __m128i *)SHA_INIT1);")
    c.dedent()
    c.write("}")
    c.write("")

    c.write("static void key_schedule_fold(void) {")
    c.indent()
    c.write("for (uint32_t off = 0; off < POOL_HASH_BYTES; off += 16) {")
    c.indent()
    c.write("__m128i m = _mm_loadu_si128((const __m128i *)(pool_small + off));")
    c.write("sha_s0 = _mm_sha256rnds2_epu32(sha_s0, sha_s1, m);")
    c.write("__m128i sh = _mm_shuffle_epi32(m, 0x0e);")
    c.write("sha_s1 = _mm_sha256rnds2_epu32(sha_s1, sha_s0, sh);")
    c.dedent()
    c.write("}")
    c.dedent()
    c.write("}")
    c.write("")

    c.write("static uint32_t apply_perm_stage(uint32_t x, const StageSpec *s) {")
    c.indent()
    c.write("for (uint8_t i = 0; i < s->op_count; i++) {")
    c.indent()
    c.write("uint8_t kind = s->op_kind[i];")
    c.write("uint32_t cst = (uint32_t)pool_small[s->op_small_addr[i] & POOL_SMALL_ADDR_MASK];")
    c.write("for (uint8_t j = 0; j < PERM_LARGE_XOR_COUNT; j++) {")
    c.indent()
    c.write("cst ^= (uint32_t)pool_large[s->op_large_addr[i][j] & POOL_LARGE_ADDR_MASK];")
    c.dedent()
    c.write("}")
    c.write("if (kind == 0) {")
    c.indent()
    c.write("x += cst;")
    c.dedent()
    c.write("} else if (kind == 1) {")
    c.indent()
    c.write("x = rol32(x, cst);")
    c.dedent()
    c.write("} else if (kind == 2) {")
    c.indent()
    c.write("x *= (cst | 1u);")
    c.dedent()
    c.write("} else if (kind == 3) {")
    c.indent()
    c.write("x ^= cst;")
    c.dedent()
    c.write("} else {")
    c.indent()
    c.write("fprintf(stderr, \"invalid perm op kind: %u\\n\", (unsigned)kind);")
    c.write("exit(1);")
    c.dedent()
    c.write("}")
    c.dedent()
    c.write("}")
    c.write("return x;")
    c.dedent()
    c.write("}")
    c.write("")

    c.write("static uint32_t apply_sha_stage(uint32_t x, const StageSpec *s) {")
    c.indent()
    c.write("__m128i m = _mm_set1_epi32((int)(x ^ s->mix_const));")
    c.write("for (uint8_t i = 0; i < s->rounds; i++) {")
    c.indent()
    c.write("sha_s0 = _mm_sha256rnds2_epu32(sha_s0, sha_s1, m);")
    c.write("__m128i sh = _mm_shuffle_epi32(m, 0x0e);")
    c.write("sha_s1 = _mm_sha256rnds2_epu32(sha_s1, sha_s0, sh);")
    c.dedent()
    c.write("}")
    c.write("uint32_t words0[4];")
    c.write("uint32_t words1[4];")
    c.write("_mm_storeu_si128((__m128i *)words0, sha_s0);")
    c.write("_mm_storeu_si128((__m128i *)words1, sha_s1);")
    c.write("uint32_t y0 = words0[s->idx0 & 3];")
    c.write("uint32_t y1 = words1[s->idx1 & 3];")
    c.write("uint32_t y = rol32(y0 ^ y1, s->rot);")
    c.write("y ^= s->xor_const;")
    c.write("return y;")
    c.dedent()
    c.write("}")
    c.write("")

    c.write("static uint32_t apply_pool_mutation_stage(uint32_t x, const StageSpec *s) {")
    c.indent()
    c.write("if (s->pool_kind == 0) {")
    c.indent()
    c.write("uint32_t addr = x & POOL_SMALL_ADDR_MASK;")
    c.write("if (addr >= POOL_SMALL_SIZE - 4096u) addr -= 4096u;")
    c.write("uint8_t fill = pool_small[addr] ^ (uint8_t)(x >> 24);")
    c.write("memset(pool_small + addr, (int)fill, s->pool_len);")
    c.dedent()
    c.write("} else {")
    c.indent()
    c.write("uint32_t addr = x & POOL_LARGE_ADDR_MASK;")
    c.write("if (addr >= POOL_LARGE_SIZE - 4096u) addr -= 4096u;")
    c.write("uint8_t fill = pool_large[addr] ^ (uint8_t)(x >> 24);")
    c.write("memset(pool_large + addr, (int)fill, s->pool_len);")
    c.dedent()
    c.write("}")
    c.write("return x;")
    c.dedent()
    c.write("}")
    c.write("")

    c.write("static uint32_t apply_stage_chain(uint32_t x, uint32_t stage_offset, uint16_t stage_count) {")
    c.indent()
    c.write("for (uint32_t i = 0; i < stage_count; i++) {")
    c.indent()
    c.write("const StageSpec *s = &STAGE_SPECS[stage_offset + i];")
    c.write("if (s->kind == 0) {")
    c.indent()
    c.write("x = apply_sha_stage(x, s);")
    c.dedent()
    c.write("} else if (s->kind == 1) {")
    c.indent()
    c.write("x = apply_perm_stage(x, s);")
    c.dedent()
    c.write("} else if (s->kind == 2) {")
    c.indent()
    c.write("continue;")
    c.dedent()
    c.write("} else {")
    c.indent()
    c.write("fprintf(stderr, \"invalid stage kind: %u\\n\", (unsigned)s->kind);")
    c.write("exit(1);")
    c.dedent()
    c.write("}")
    c.dedent()
    c.write("}")
    c.write("return x;")
    c.dedent()
    c.write("}")
    c.write("")

    c.write("static uint32_t apply_pool_stage_chain(uint32_t x, uint32_t stage_offset, uint16_t stage_count) {")
    c.indent()
    c.write("for (uint32_t i = 0; i < stage_count; i++) {")
    c.indent()
    c.write("const StageSpec *s = &STAGE_SPECS[stage_offset + i];")
    c.write("if (s->kind == 2) {")
    c.indent()
    c.write("x = apply_pool_mutation_stage(x, s);")
    c.dedent()
    c.write("}")
    c.dedent()
    c.write("}")
    c.write("return x;")
    c.dedent()
    c.write("}")
    c.write("")

    c.write("static int split_tokens(char *line, char **tok, int max_tok) {")
    c.indent()
    c.write("int n = 0;")
    c.write("char *save = NULL;")
    c.write("for (char *p = strtok_r(line, \" \\t\\r\\n\", &save); p && n < max_tok; p = strtok_r(NULL, \" \\t\\r\\n\", &save)) {")
    c.indent()
    c.write("tok[n++] = p;")
    c.dedent()
    c.write("}")
    c.write("return n;")
    c.dedent()
    c.write("}")
    c.write("")

    c.write("static int parse_load_segments(const char *binary, LoadSeg *segs, int max_segs) {")
    c.indent()
    c.write("char cmd[1024];")
    c.write("snprintf(cmd, sizeof(cmd), \"readelf -W -l '%s'\", binary);")
    c.write("FILE *fp = popen(cmd, \"r\");")
    c.write("if (!fp) return -1;")
    c.write("char line[2048];")
    c.write("int count = 0;")
    c.write("while (fgets(line, sizeof(line), fp)) {")
    c.indent()
    c.write("char buf[2048];")
    c.write("strncpy(buf, line, sizeof(buf) - 1);")
    c.write("buf[sizeof(buf) - 1] = '\\0';")
    c.write("char *tok[16];")
    c.write("int nt = split_tokens(buf, tok, 16);")
    c.write("if (nt < 6) continue;")
    c.write("if (strcmp(tok[0], \"LOAD\") != 0) continue;")
    c.write("if (count >= max_segs) { pclose(fp); return -1; }")
    c.write("uint64_t off = strtoull(tok[1], NULL, 16);")
    c.write("uint64_t vaddr = strtoull(tok[2], NULL, 16);")
    c.write("uint64_t filesz = strtoull(tok[4], NULL, 16);")
    c.write("segs[count].vstart = vaddr;")
    c.write("segs[count].vend = vaddr + filesz;")
    c.write("segs[count].file_off = off;")
    c.write("count++;")
    c.dedent()
    c.write("}")
    c.write("pclose(fp);")
    c.write("return count;")
    c.dedent()
    c.write("}")
    c.write("")

    c.write("static int parse_segment_addrs(const char *binary, uint64_t *starts, uint64_t *ends, int count) {")
    c.indent()
    c.write("for (int i = 0; i < count; i++) { starts[i] = UINT64_MAX; ends[i] = UINT64_MAX; }")
    c.write("char cmd[1024];")
    c.write("snprintf(cmd, sizeof(cmd), \"nm -n '%s'\", binary);")
    c.write("FILE *fp = popen(cmd, \"r\");")
    c.write("if (!fp) return -1;")
    c.write("char line[2048];")
    c.write("while (fgets(line, sizeof(line), fp)) {")
    c.indent()
    c.write("unsigned long long addr = 0;")
    c.write("char typ = 0;")
    c.write("int idx = -1;")
    c.write("char suffix[32] = {0};")
    c.write('if (sscanf(line, "%llx %c segment%d%31s", &addr, &typ, &idx, suffix) < 3) continue;')
    c.write("if (idx < 0 || idx >= count) continue;")
    c.write('if (suffix[0] == \'\\0\') {')
    c.indent()
    c.write("starts[idx] = (uint64_t)addr;")
    c.dedent()
    c.write('} else if (strcmp(suffix, "_end") == 0) {')
    c.indent()
    c.write("ends[idx] = (uint64_t)addr;")
    c.dedent()
    c.write("}")
    c.dedent()
    c.write("}")
    c.write("pclose(fp);")
    c.write("for (int i = 0; i < count; i++) {")
    c.indent()
    c.write("if (starts[i] == UINT64_MAX || ends[i] == UINT64_MAX) return -1;")
    c.dedent()
    c.write("}")
    c.write("return 0;")
    c.dedent()
    c.write("}")
    c.write("")

    c.write("static uint64_t vaddr_to_offset(uint64_t vaddr, const LoadSeg *segs, int nsegs) {")
    c.indent()
    c.write("for (int i = 0; i < nsegs; i++) {")
    c.indent()
    c.write("if (segs[i].vstart <= vaddr && vaddr < segs[i].vend) {")
    c.indent()
    c.write("return segs[i].file_off + (vaddr - segs[i].vstart);")
    c.dedent()
    c.write("}")
    c.dedent()
    c.write("}")
    c.write("fprintf(stderr, \"address 0x%llx not in file-backed LOAD segment\\n\", (unsigned long long)vaddr);")
    c.write("exit(1);")
    c.dedent()
    c.write("}")
    c.write("")

    c.write("static uint8_t *read_file(const char *path, size_t *out_size) {")
    c.indent()
    c.write("FILE *fp = fopen(path, \"rb\");")
    c.write("if (!fp) return NULL;")
    c.write("if (fseek(fp, 0, SEEK_END) != 0) { fclose(fp); return NULL; }")
    c.write("long sz = ftell(fp);")
    c.write("if (sz < 0) { fclose(fp); return NULL; }")
    c.write("if (fseek(fp, 0, SEEK_SET) != 0) { fclose(fp); return NULL; }")
    c.write("uint8_t *buf = (uint8_t *)malloc((size_t)sz);")
    c.write("if (!buf) { fclose(fp); return NULL; }")
    c.write("if (fread(buf, 1, (size_t)sz, fp) != (size_t)sz) { fclose(fp); free(buf); return NULL; }")
    c.write("fclose(fp);")
    c.write("*out_size = (size_t)sz;")
    c.write("return buf;")
    c.dedent()
    c.write("}")
    c.write("")

    c.write("static int write_file(const char *path, const uint8_t *buf, size_t size) {")
    c.indent()
    c.write("FILE *fp = fopen(path, \"wb\");")
    c.write("if (!fp) return -1;")
    c.write("size_t w = fwrite(buf, 1, size, fp);")
    c.write("fclose(fp);")
    c.write("return w == size ? 0 : -1;")
    c.dedent()
    c.write("}")
    c.write("")

    c.write("int main(int argc, char **argv) {")
    c.indent()
    c.write("if (argc != 4) {")
    c.indent()
    c.write("fprintf(stderr, \"Usage: %s <unpacked> <secret_input> <packed_out>\\n\", argv[0]);")
    c.write("return 1;")
    c.dedent()
    c.write("}")
    c.write("const char *unpacked_path = argv[1];")
    c.write("const char *secret_path = argv[2];")
    c.write("const char *packed_path = argv[3];")

    c.write("size_t secret_size = 0;")
    c.write("uint8_t *secret = read_file(secret_path, &secret_size);")
    c.write("if (!secret) { fprintf(stderr, \"failed to read secret input\\n\"); return 1; }")
    c.write("if (secret_size < (size_t)(2 * NSEGMENTS)) {")
    c.indent()
    c.write("fprintf(stderr, \"secret input too short: got %zu expected at least %d\\n\", secret_size, 2 * NSEGMENTS);")
    c.write("free(secret);")
    c.write("return 1;")
    c.dedent()
    c.write("}")

    c.write("LoadSeg loadsegs[16];")
    c.write("int nload = parse_load_segments(unpacked_path, loadsegs, 16);")
    c.write("if (nload <= 0) { fprintf(stderr, \"failed to parse LOAD segments\\n\"); free(secret); return 1; }")

    c.write("uint64_t seg_start[NSEGMENTS + 2];")
    c.write("uint64_t seg_end[NSEGMENTS + 2];")
    c.write("if (parse_segment_addrs(unpacked_path, seg_start, seg_end, NSEGMENTS + 2) != 0) {")
    c.indent()
    c.write("fprintf(stderr, \"failed to parse segment symbols\\n\");")
    c.write("free(secret);")
    c.write("return 1;")
    c.dedent()
    c.write("}")

    c.write("uint64_t seg_off[NSEGMENTS + 2];")
    c.write("for (int i = 0; i < NSEGMENTS + 2; i++) {")
    c.indent()
    c.write("seg_off[i] = vaddr_to_offset(seg_start[i], loadsegs, nload);")
    c.dedent()
    c.write("}")

    c.write("size_t seg_len[NSEGMENTS + 2];")
    c.write("for (int i = 0; i < NSEGMENTS + 2; i++) {")
    c.indent()
    c.write("uint64_t end_off = vaddr_to_offset(seg_end[i], loadsegs, nload);")
    c.write("if (end_off < seg_off[i]) {")
    c.indent()
    c.write("fprintf(stderr, \"segment offsets out of order at %d\\n\", i);")
    c.write("free(secret);")
    c.write("return 1;")
    c.dedent()
    c.write("}")
    c.write("seg_len[i] = (size_t)(end_off - seg_off[i]);")
    c.dedent()
    c.write("}")

    c.write("size_t binary_size = 0;")
    c.write("uint8_t *binary = read_file(unpacked_path, &binary_size);")
    c.write("if (!binary) { fprintf(stderr, \"failed to read unpacked binary\\n\"); free(secret); return 1; }")

    c.write("uint8_t *masks[NSEGMENTS + 1];")
    c.write("memset(masks, 0, sizeof(masks));")
    c.write("for (int t = 1; t <= NSEGMENTS; t++) {")
    c.indent()
    c.write("masks[t] = (uint8_t *)calloc(seg_len[t], 1);")
    c.write("if (!masks[t]) { fprintf(stderr, \"alloc failed for mask %d\\n\", t); free(binary); free(secret); return 1; }")
    c.dedent()
    c.write("}")

    c.write("init_sha_state();")

    c.write("for (int seg = 0; seg < NSEGMENTS; seg++) {")
    c.indent()
    c.write("key_schedule_fold();")
    c.write("uint32_t in16 = (uint32_t)secret[2 * seg] | ((uint32_t)secret[2 * seg + 1] << 8);")
    c.write("uint32_t x = in16 | (in16 << 16);")
    c.write("const SegmentSpec *ss = &SEGMENT_SPECS[seg];")
    c.write("size_t stream_off = 0;")
    c.write("for (uint32_t ti = 0; ti < ss->target_count; ti++) {")
    c.indent()
    c.write("const TargetSpec *ts = &TARGET_SPECS[ss->target_offset + ti];")
    c.write("uint32_t target = ts->target_index;")
    c.write("size_t len = seg_len[target];")
    c.write("if (stream_off + STREAM_PREFIX_LEN > STREAM_BUFFER_SIZE) {")
    c.indent()
    c.write('fprintf(stderr, "stream buffer overflow in segment %d\\n", seg);')
    c.write("free(binary);")
    c.write("free(secret);")
    c.write("for (int t = 1; t <= NSEGMENTS; t++) free(masks[t]);")
    c.write("return 1;")
    c.dedent()
    c.write("}")
    c.write(f"memset(stream_buf + stream_off, 0, {STREAM_PREFIX_LEN}u);")
    c.write("for (uint8_t pass = 0; pass < ts->prefix_pass_count; pass++) {")
    c.indent()
    c.write("const PassSpec *ps = &PASS_SPECS[ts->prefix_pass_offset + pass];")
    c.write(f"for (size_t j = 0; j < {STREAM_PREFIX_LEN}u; j++) {{")
    c.indent()
    c.write("x = apply_stage_chain(x, ps->stage_offset, ps->stage_count);")
    c.write("stream_buf[stream_off + j] ^= (uint8_t)x;")
    c.dedent()
    c.write("}")
    c.write("if (pass + 1 != ts->prefix_pass_count) {")
    c.indent()
    c.write("x = apply_pool_stage_chain(x, ps->stage_offset, ps->stage_count);")
    c.dedent()
    c.write("}")
    c.dedent()
    c.write("}")
    c.write(f"stream_off += {STREAM_PREFIX_LEN}u;")
    c.dedent()
    c.write("}")
    c.write("stream_off = 0;")
    c.write("for (uint32_t ti = 0; ti < ss->target_count; ti++) {")
    c.indent()
    c.write("const TargetSpec *ts = &TARGET_SPECS[ss->target_offset + ti];")
    c.write("uint32_t target = ts->target_index;")
    c.write("size_t len = seg_len[target];")
    c.write("uint8_t *mask = masks[target];")
    c.write("for (size_t j = 0; j < len; j++) {")
    c.indent()
    c.write(f"mask[j] ^= stream_buf[stream_off + (j % {STREAM_PREFIX_LEN}u)];")
    c.dedent()
    c.write("}")
    c.write(f"stream_off += {STREAM_PREFIX_LEN}u;")
    c.dedent()
    c.write("}")
    c.dedent()
    c.write("}")

    c.write("for (int target = NSEGMENTS; target >= 1; target--) {")
    c.indent()
    c.write("uint64_t off = seg_off[target];")
    c.write("size_t len = seg_len[target];")
    c.write("if (off + len > binary_size) {")
    c.indent()
    c.write("fprintf(stderr, \"target segment %d exceeds binary file size\\n\", target);")
    c.write("free(binary);")
    c.write("free(secret);")
    c.write("for (int t = 1; t <= NSEGMENTS; t++) free(masks[t]);")
    c.write("return 1;")
    c.dedent()
    c.write("}")
    c.write("for (size_t j = 0; j < len; j++) {")
    c.indent()
    c.write("binary[off + j] ^= masks[target][j];")
    c.dedent()
    c.write("}")
    c.dedent()
    c.write("}")

    c.write("if (write_file(packed_path, binary, binary_size) != 0) {")
    c.indent()
    c.write("fprintf(stderr, \"failed writing packed output\\n\");")
    c.write("free(binary);")
    c.write("free(secret);")
    c.write("for (int t = 1; t <= NSEGMENTS; t++) free(masks[t]);")
    c.write("return 1;")
    c.dedent()
    c.write("}")

    c.write('printf("[encryptor] packed %s -> %s with %d segments\\n", unpacked_path, packed_path, NSEGMENTS);')

    c.write("for (int t = 1; t <= NSEGMENTS; t++) free(masks[t]);")
    c.write("free(binary);")
    c.write("free(secret);")
    c.write("return 0;")
    c.dedent()
    c.write("}")


def emit_runtime_rol_inline(c: CodeWriter, xvar: str, rot: int):
    if rot <= 0 or rot >= 32:
        raise RuntimeError(f"invalid rotate amount: {rot}")
    c.write(f"{xvar} = ({xvar} << {rot}u) | ({xvar} >> {32 - rot}u);")


def emit_runtime_sha_stage_inline(c: CodeWriter, stage: StageSpec, xvar: str):
    c.write("{")
    c.indent()
    c.write(f"__m128i sha_m = _mm_set1_epi32((int)({xvar} ^ 0x{stage.mix_const:08x}u));")
    c.write(f"for (uint32_t sha_i = 0; sha_i < {stage.rounds}u; sha_i++) {{")
    c.indent()
    c.write("sha_s0 = _mm_sha256rnds2_epu32(sha_s0, sha_s1, sha_m);")
    c.write("__m128i sha_sh = _mm_shuffle_epi32(sha_m, 0x0e);")
    c.write("sha_s1 = _mm_sha256rnds2_epu32(sha_s1, sha_s0, sha_sh);")
    c.dedent()
    c.write("}")
    c.write("uint32_t sha_words0[4];")
    c.write("uint32_t sha_words1[4];")
    c.write("_mm_storeu_si128((__m128i *)sha_words0, sha_s0);")
    c.write("_mm_storeu_si128((__m128i *)sha_words1, sha_s1);")
    c.write(f"uint32_t sha_mix = sha_words0[{stage.idx0}] ^ sha_words1[{stage.idx1}];")
    emit_runtime_rol_inline(c, "sha_mix", stage.rot)
    c.write(f"{xvar} = sha_mix ^ 0x{stage.xor_const:08x}u;")
    c.dedent()
    c.write("}")


def emit_runtime_pool_mutation_inline(c: CodeWriter, xvar: str, pool_len: int):
    raise RuntimeError("emit_runtime_pool_mutation_inline requires pool_kind")


def emit_runtime_pool_mutation_inline_with_kind(
    c: CodeWriter, xvar: str, pool_len: int, pool_kind: int
):
    c.write("{")
    c.indent()
    if pool_kind == 0:
        c.write(f"uint32_t pool_addr = {xvar} & POOL_SMALL_ADDR_MASK;")
        c.write("if (pool_addr >= POOL_SMALL_SIZE - 4096u) pool_addr -= 4096u;")
        c.write(f"uint8_t pool_fill = pool_small[pool_addr] ^ (uint8_t)({xvar} >> 24);")
        c.write("uint8_t *pool_dst = pool_small + pool_addr;")
    else:
        c.write(f"uint32_t pool_addr = {xvar} & POOL_LARGE_ADDR_MASK;")
        c.write("if (pool_addr >= POOL_LARGE_SIZE - 4096u) pool_addr -= 4096u;")
        c.write(f"uint8_t pool_fill = pool_large[pool_addr] ^ (uint8_t)({xvar} >> 24);")
        c.write("uint8_t *pool_dst = pool_large + pool_addr;")
    c.write(f"size_t pool_len_bytes = {pool_len}u;")
    c.write(
        '__asm__ volatile("cld; rep stosb" : "+D"(pool_dst), "+c"(pool_len_bytes) : "a"(pool_fill) : "memory");'
    )
    c.dedent()
    c.write("}")


def emit_runtime_key_schedule_inline(c: CodeWriter):
    c.write("{")
    c.indent()
    c.write("for (uint32_t keysched_off = 0; keysched_off < POOL_HASH_BYTES; keysched_off += 16u) {")
    c.indent()
    c.write("__m128i keysched_m = _mm_loadu_si128((const __m128i *)(pool_small + keysched_off));")
    c.write("sha_s0 = _mm_sha256rnds2_epu32(sha_s0, sha_s1, keysched_m);")
    c.write("__m128i keysched_sh = _mm_shuffle_epi32(keysched_m, 0x0e);")
    c.write("sha_s1 = _mm_sha256rnds2_epu32(sha_s1, sha_s0, keysched_sh);")
    c.dedent()
    c.write("}")
    c.dedent()
    c.write("}")


def emit_runtime_stage_inline(c: CodeWriter, stage: StageSpec, xvar: str):
    if stage.kind == "sha":
        emit_runtime_sha_stage_inline(c, stage, xvar)
        return
    if stage.kind == "perm":
        for kind, small_addr, large_addrs in stage.perm_ops:
            c.write("{")
            c.indent()
            c.write(
                f"uint32_t perm_cst = (uint32_t)pool_small[0x{small_addr:04x}u & POOL_SMALL_ADDR_MASK];"
            )
            for large_addr in large_addrs:
                c.write(
                    f"perm_cst ^= (uint32_t)pool_large[0x{large_addr:06x}u & POOL_LARGE_ADDR_MASK];"
                )
            if kind == PERM_OP_ADD:
                c.write(f"{xvar} += perm_cst;")
            elif kind == PERM_OP_ROL:
                c.write("uint32_t perm_rot = perm_cst & 31u;")
                c.write("if (perm_rot != 0) {")
                c.indent()
                c.write(f"{xvar} = ({xvar} << perm_rot) | ({xvar} >> (32u - perm_rot));")
                c.dedent()
                c.write("}")
            elif kind == PERM_OP_MUL:
                c.write(f"{xvar} *= (perm_cst | 1u);")
            elif kind == PERM_OP_XOR:
                c.write(f"{xvar} ^= perm_cst;")
            else:
                raise RuntimeError(f"unsupported perm op kind: {kind}")
            c.dedent()
            c.write("}")
        return
    if stage.kind == "pool_mutation":
        return
    raise RuntimeError(f"unsupported stage kind: {stage.kind}")


def emit_runtime_interloop_pool(
    c: CodeWriter, stages: tuple[StageSpec, ...], xvar: str
):
    for stage in stages:
        if stage.kind == "pool_mutation":
            emit_runtime_pool_mutation_inline_with_kind(
                c, xvar, stage.pool_len, stage.pool_kind
            )


def emit_runtime_dummy_locals(
    c: CodeWriter, seg: int, xvar: str, localspecs: tuple[DummyLocalSpec, ...]
):
    if not localspecs:
        return

    names: list[str] = []
    for idx, spec in enumerate(localspecs):
        name = f"dummy_local_{seg}_{idx}"
        names.append(name)
        c.write(
            f"volatile {spec.c_type} {name}[{spec.count}] __attribute__((aligned({spec.align})));"
        )
    c.write(f"uint32_t dummy_mix_{seg} = 0u;")
    for idx, spec in enumerate(localspecs):
        name = names[idx]
        c.write(
            f"{name}[{spec.idx0}] = ({spec.c_type})({xvar} ^ 0x{spec.init_const:08x}u);"
        )
        c.write(
            f"{name}[{spec.idx1}] = ({spec.c_type})({name}[{spec.idx0}] + ({spec.c_type})0x{spec.mix_const:08x}u);"
        )
        c.write(f"dummy_mix_{seg} ^= (uint32_t){name}[{spec.idx1}];")

    asm_inputs = [f'\"r\"(dummy_mix_{seg})']
    asm_inputs.extend(f'\"m\"({name})' for name in names)
    c.write(
        '__asm__ volatile("" : : '
        + ", ".join(asm_inputs)
        + ' : "memory");'
    )


def emit_runtime_c(
    c: CodeWriter,
    nsegments: int,
    flag: str,
    sha_init0: list[int],
    sha_init1: list[int],
    specs: list[SegmentSpec],
):
    c.write("#define _GNU_SOURCE")
    c.write("#include <immintrin.h>")
    c.write("#include <stdint.h>")
    c.write("#include <stddef.h>")
    c.write("#include <stdio.h>")
    c.write("#include <string.h>")
    c.write("#include <unistd.h>")
    c.write("#include <sys/mman.h>")
    c.write("")
    c.write(f"#define NSEGMENTS {nsegments}")
    c.write(f"#define POOL_SMALL_SIZE {POOL_SMALL_SIZE}u")
    c.write(f"#define POOL_SMALL_ADDR_MASK 0x{POOL_SMALL_ADDR_MASK:08x}u")
    c.write(f"#define POOL_LARGE_SIZE {POOL_LARGE_SIZE}u")
    c.write(f"#define POOL_LARGE_ADDR_MASK 0x{POOL_LARGE_ADDR_MASK:08x}u")
    c.write(f"#define POOL_HASH_BYTES {POOL_HASH_BYTES}u")
    c.write(f"#define STREAM_BUFFER_ADDR 0x{STREAM_BUFFER_ADDR:08x}u")
    c.write(f"#define STREAM_BUFFER_SIZE 0x{STREAM_BUFFER_SIZE:08x}u")
    c.write(f"#define STREAM_PREFIX_LEN {STREAM_PREFIX_LEN}u")
    c.write("")

    c.write("static const uint8_t SHA_INIT0[16] = {")
    c.indent()
    c.write(", ".join(f"0x{x:02x}" for x in sha_init0))
    c.dedent()
    c.write("};")
    c.write("static const uint8_t SHA_INIT1[16] = {")
    c.indent()
    c.write(", ".join(f"0x{x:02x}" for x in sha_init1))
    c.dedent()
    c.write("};")
    c.write("")
    c.write("static __m128i sha_s0;")
    c.write("static __m128i sha_s1;")
    c.write("static uint8_t *stream_buf_ptr;")
    c.write("static uint8_t pool_small[POOL_SMALL_SIZE] __attribute__((aligned(64)));")
    c.write("static uint8_t pool_large[POOL_LARGE_SIZE] __attribute__((aligned(64)));")
    c.write("")

    for i in range(nsegments + 2):
        c.write(f"extern char segment{i}_end[];")
    for i in range(nsegments + 2):
        c.write(f"__attribute__((noinline, used)) void segment{i}(void);")
    c.write("__attribute__((noinline, used)) void *run(void **addrs);")
    c.write("")

    for seg, spec in enumerate(specs):
        target = spec.targets[0]
        dummy_locals = random_segment_dummy_locals()
        c.write(f"__attribute__((noinline, used)) void segment{seg}(void) {{")
        c.indent()
        emit_runtime_key_schedule_inline(c)
        c.write("uint8_t in0 = 0;")
        c.write("uint8_t in1 = 0;")
        c.write("(void)read(0, &in0, 1);")
        c.write("(void)read(0, &in1, 1);")
        c.write("uint32_t in16 = (uint32_t)in0 | ((uint32_t)in1 << 8);")
        c.write("uint32_t x = in16 | (in16 << 16);")
        emit_runtime_dummy_locals(c, seg, "x", dummy_locals)
        c.write("uint8_t *stream_buf = stream_buf_ptr;")
        c.write(f"uint8_t *target_ptr = (uint8_t *)(uintptr_t)(void *)segment{target.target_index};")
        c.write(
            f"size_t target_len = (size_t)((uintptr_t)segment{target.target_index}_end - "
            f"(uintptr_t)(void *)segment{target.target_index});"
        )
        c.write("memset(stream_buf, 0, STREAM_PREFIX_LEN);")
        for pass_idx, pass_stages in enumerate(target.prefix_passes):
            c.write("{")
            c.indent()
            c.write("for (size_t j = 0; j < STREAM_PREFIX_LEN; j++) {")
            c.indent()
            for stage in pass_stages:
                emit_runtime_stage_inline(c, stage, "x")
            c.write("stream_buf[j] ^= (uint8_t)x;")
            c.dedent()
            c.write("}")
            if pass_idx + 1 != len(target.prefix_passes):
                emit_runtime_interloop_pool(c, pass_stages, "x")
            c.dedent()
            c.write("}")
        c.write("for (size_t j = 0; j < target_len; j++) {")
        c.indent()
        c.write("target_ptr[j] ^= stream_buf[j % STREAM_PREFIX_LEN];")
        c.dedent()
        c.write("}")
        c.write(f'__asm__ __volatile__(".globl segment{seg}_end\\nsegment{seg}_end:");')
        c.write(f"segment{target.target_index}();")
        c.dedent()
        c.write("}")
        c.write("")

    c.write(f"__attribute__((noinline, used)) void segment{nsegments}(void) {{")
    c.indent()
    message = (
        "Congratulations! Please submit the following token to get the flag: "
        f"{flag}"
    )
    for ch in message:
        c.write(f"putchar({ord(ch)});")
    c.write(f'__asm__ __volatile__(".globl segment{nsegments}_end\\nsegment{nsegments}_end:");')
    c.write(f"segment{nsegments + 1}();")
    c.dedent()
    c.write("}")
    c.write("")

    c.write(f"__attribute__((noinline, used)) void segment{nsegments + 1}(void) {{")
    c.indent()
    c.write(f'__asm__ __volatile__(".globl segment{nsegments + 1}_end\\nsegment{nsegments + 1}_end:");')
    c.write("return;")
    c.dedent()
    c.write("}")
    c.write("")

    c.write("__attribute__((noinline, used)) void *run(void **addrs) {")
    c.indent()
    c.write("if (!addrs) return (void *)(uintptr_t)segment0;")
    for i in range(nsegments + 1):
        c.write(f"addrs[{i}] = (void *)(uintptr_t)segment{i};")
    c.write(
        "stream_buf_ptr = (uint8_t *)mmap((void *)(uintptr_t)STREAM_BUFFER_ADDR, "
        "STREAM_BUFFER_SIZE, PROT_READ | PROT_WRITE, "
        "MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED, -1, 0);"
    )
    c.write("sha_s0 = _mm_loadu_si128((const __m128i *)SHA_INIT0);")
    c.write("sha_s1 = _mm_loadu_si128((const __m128i *)SHA_INIT1);")
    c.write("segment0();")
    c.write(f"return (void *)(uintptr_t)segment{nsegments + 1};")
    c.dedent()
    c.write("}")
    c.write("")

    c.write("__attribute__((used)) int main(void) {")
    c.indent()
    c.write("uintptr_t code_lo = ((uintptr_t)run(NULL)) & ~(uintptr_t)0xfff;")
    c.write(
        f"uintptr_t code_hi = (((uintptr_t)segment{nsegments + 1}_end) + 0xfff) & ~(uintptr_t)0xfff;"
    )
    c.write("if (code_hi > code_lo) {")
    c.indent()
    c.write(
        "mprotect((void *)code_lo, (size_t)(code_hi - code_lo), "
        "PROT_READ | PROT_WRITE | PROT_EXEC);"
    )
    c.dedent()
    c.write("}")
    c.write("void *addrs[NSEGMENTS + 1];")
    c.write("(void)run(addrs);")
    c.write("return 0;")
    c.dedent()
    c.write("}")
    c.write("")
    return

    c.write("static uint64_t vaddr_to_offset(uint64_t vaddr, const LoadSeg *segs, int nsegs) {")
    c.indent()
    c.write("for (int i = 0; i < nsegs; i++) {")
    c.indent()
    c.write("if (segs[i].vstart <= vaddr && vaddr < segs[i].vend) {")
    c.indent()
    c.write("return segs[i].file_off + (vaddr - segs[i].vstart);")
    c.dedent()
    c.write("}")
    c.dedent()
    c.write("}")
    c.write("fprintf(stderr, \"address 0x%llx not in file-backed LOAD segment\\n\", (unsigned long long)vaddr);")
    c.write("exit(1);")
    c.dedent()
    c.write("}")
    c.write("")

    c.write("static uint8_t *read_file(const char *path, size_t *out_size) {")
    c.indent()
    c.write("FILE *fp = fopen(path, \"rb\");")
    c.write("if (!fp) return NULL;")
    c.write("if (fseek(fp, 0, SEEK_END) != 0) { fclose(fp); return NULL; }")
    c.write("long sz = ftell(fp);")
    c.write("if (sz < 0) { fclose(fp); return NULL; }")
    c.write("if (fseek(fp, 0, SEEK_SET) != 0) { fclose(fp); return NULL; }")
    c.write("uint8_t *buf = (uint8_t *)malloc((size_t)sz);")
    c.write("if (!buf) { fclose(fp); return NULL; }")
    c.write("if (fread(buf, 1, (size_t)sz, fp) != (size_t)sz) { fclose(fp); free(buf); return NULL; }")
    c.write("fclose(fp);")
    c.write("*out_size = (size_t)sz;")
    c.write("return buf;")
    c.dedent()
    c.write("}")
    c.write("")

    c.write("static int write_file(const char *path, const uint8_t *buf, size_t size) {")
    c.indent()
    c.write("FILE *fp = fopen(path, \"wb\");")
    c.write("if (!fp) return -1;")
    c.write("size_t w = fwrite(buf, 1, size, fp);")
    c.write("fclose(fp);")
    c.write("return w == size ? 0 : -1;")
    c.dedent()
    c.write("}")
    c.write("")

    c.write("int main(int argc, char **argv) {")
    c.indent()
    c.write("if (argc != 4) {")
    c.indent()
    c.write("fprintf(stderr, \"Usage: %s <unpacked> <secret_input> <packed_out>\\n\", argv[0]);")
    c.write("return 1;")
    c.dedent()
    c.write("}")
    c.write("const char *unpacked_path = argv[1];")
    c.write("const char *secret_path = argv[2];")
    c.write("const char *packed_path = argv[3];")

    c.write("size_t secret_size = 0;")
    c.write("uint8_t *secret = read_file(secret_path, &secret_size);")
    c.write("if (!secret) { fprintf(stderr, \"failed to read secret input\\n\"); return 1; }")
    c.write("if (secret_size < (size_t)(2 * NSEGMENTS)) {")
    c.indent()
    c.write("fprintf(stderr, \"secret input too short: got %zu expected at least %d\\n\", secret_size, 2 * NSEGMENTS);")
    c.write("free(secret);")
    c.write("return 1;")
    c.dedent()
    c.write("}")

    c.write("LoadSeg loadsegs[16];")
    c.write("int nload = parse_load_segments(unpacked_path, loadsegs, 16);")
    c.write("if (nload <= 0) { fprintf(stderr, \"failed to parse LOAD segments\\n\"); free(secret); return 1; }")

    c.write("uint64_t seg_start[NSEGMENTS + 2];")
    c.write("uint64_t seg_end[NSEGMENTS + 2];")
    c.write("if (parse_segment_addrs(unpacked_path, seg_start, seg_end, NSEGMENTS + 2) != 0) {")
    c.indent()
    c.write("fprintf(stderr, \"failed to parse segment symbols\\n\");")
    c.write("free(secret);")
    c.write("return 1;")
    c.dedent()
    c.write("}")

    c.write("uint64_t seg_off[NSEGMENTS + 2];")
    c.write("for (int i = 0; i < NSEGMENTS + 2; i++) {")
    c.indent()
    c.write("seg_off[i] = vaddr_to_offset(seg_start[i], loadsegs, nload);")
    c.dedent()
    c.write("}")

    c.write("size_t seg_len[NSEGMENTS + 2];")
    c.write("for (int i = 0; i < NSEGMENTS + 2; i++) {")
    c.indent()
    c.write("uint64_t end_off = vaddr_to_offset(seg_end[i], loadsegs, nload);")
    c.write("if (end_off < seg_off[i]) {")
    c.indent()
    c.write("fprintf(stderr, \"segment offsets out of order at %d\\n\", i);")
    c.write("free(secret);")
    c.write("return 1;")
    c.dedent()
    c.write("}")
    c.write("seg_len[i] = (size_t)(end_off - seg_off[i]);")
    c.dedent()
    c.write("}")

    c.write("size_t binary_size = 0;")
    c.write("uint8_t *binary = read_file(unpacked_path, &binary_size);")
    c.write("if (!binary) { fprintf(stderr, \"failed to read unpacked binary\\n\"); free(secret); return 1; }")

    c.write("uint8_t *masks[NSEGMENTS + 1];")
    c.write("memset(masks, 0, sizeof(masks));")
    c.write("for (int t = 1; t <= NSEGMENTS; t++) {")
    c.indent()
    c.write("masks[t] = (uint8_t *)calloc(seg_len[t], 1);")
    c.write("if (!masks[t]) { fprintf(stderr, \"alloc failed for mask %d\\n\", t); free(binary); free(secret); return 1; }")
    c.dedent()
    c.write("}")

    c.write("init_sha_state();")

    c.write("for (int seg = 0; seg < NSEGMENTS; seg++) {")
    c.indent()
    c.write("key_schedule_fold();")
    c.write("uint32_t in16 = (uint32_t)secret[2 * seg] | ((uint32_t)secret[2 * seg + 1] << 8);")
    c.write("uint32_t x = in16 | (in16 << 16);")
    c.write("const SegmentSpec *ss = &SEGMENT_SPECS[seg];")
    c.write("size_t stream_off = 0;")
    c.write("for (uint32_t ti = 0; ti < ss->target_count; ti++) {")
    c.indent()
    c.write("const TargetSpec *ts = &TARGET_SPECS[ss->target_offset + ti];")
    c.write("uint32_t target = ts->target_index;")
    c.write("size_t len = seg_len[target];")
    c.write(f"size_t span = len < {STREAM_PREFIX_LEN}u ? {STREAM_PREFIX_LEN}u : len;")
    c.write("if (stream_off + span > STREAM_BUFFER_SIZE) {")
    c.indent()
    c.write('fprintf(stderr, "stream buffer overflow in segment %d\\n", seg);')
    c.write("free(binary);")
    c.write("free(secret);")
    c.write("for (int t = 1; t <= NSEGMENTS; t++) free(masks[t]);")
    c.write("return 1;")
    c.dedent()
    c.write("}")
    c.write(f"memset(stream_buf + stream_off, 0, {STREAM_PREFIX_LEN}u);")
    c.write("for (uint8_t pass = 0; pass + 1 < ts->loop_count; pass++) {")
    c.indent()
    c.write(f"for (size_t j = 0; j < {STREAM_PREFIX_LEN}u; j++) {{")
    c.indent()
    c.write("x = apply_target_byte(x, ts);")
    c.write("stream_buf[stream_off + j] ^= (uint8_t)x;")
    c.dedent()
    c.write("}")
    c.write("x = apply_loop_pool_mutations(x, ts);")
    c.dedent()
    c.write("}")
    c.write("for (size_t j = 0; j < span; j++) {")
    c.indent()
    c.write("x = apply_target_byte(x, ts);")
    c.write(f"if (j < {STREAM_PREFIX_LEN}u) {{")
    c.indent()
    c.write("stream_buf[stream_off + j] ^= (uint8_t)x;")
    c.dedent()
    c.write("} else {")
    c.indent()
    c.write("stream_buf[stream_off + j] = (uint8_t)x;")
    c.dedent()
    c.write("}")
    c.dedent()
    c.write("}")
    c.write("stream_off += span;")
    c.write("stream_off = 0;")
    c.write("for (uint32_t ti = 0; ti < ss->target_count; ti++) {")
    c.indent()
    c.write("const TargetSpec *ts = &TARGET_SPECS[ss->target_offset + ti];")
    c.write("uint32_t target = ts->target_index;")
    c.write("size_t len = seg_len[target];")
    c.write(f"size_t span = len < {STREAM_PREFIX_LEN}u ? {STREAM_PREFIX_LEN}u : len;")
    c.write("uint8_t *mask = masks[target];")
    c.write("for (size_t j = 0; j < len; j++) {")
    c.indent()
    c.write("mask[j] ^= stream_buf[stream_off + j];")
    c.dedent()
    c.write("}")
    c.write("stream_off += span;")
    c.dedent()
    c.write("}")
    c.dedent()
    c.write("}")
    c.dedent()
    c.write("}")

    c.write("for (int target = NSEGMENTS; target >= 1; target--) {")
    c.indent()
    c.write("uint64_t off = seg_off[target];")
    c.write("size_t len = seg_len[target];")
    c.write("if (off + len > binary_size) {")
    c.indent()
    c.write("fprintf(stderr, \"target segment %d exceeds binary file size\\n\", target);")
    c.write("free(binary);")
    c.write("free(secret);")
    c.write("for (int t = 1; t <= NSEGMENTS; t++) free(masks[t]);")
    c.write("return 1;")
    c.dedent()
    c.write("}")
    c.write("for (size_t j = 0; j < len; j++) {")
    c.indent()
    c.write("binary[off + j] ^= masks[target][j];")
    c.dedent()
    c.write("}")
    c.dedent()
    c.write("}")

    c.write("if (write_file(packed_path, binary, binary_size) != 0) {")
    c.indent()
    c.write("fprintf(stderr, \"failed writing packed output\\n\");")
    c.write("free(binary);")
    c.write("free(secret);")
    c.write("for (int t = 1; t <= NSEGMENTS; t++) free(masks[t]);")
    c.write("return 1;")
    c.dedent()
    c.write("}")

    c.write('printf("[encryptor] packed %s -> %s with %d segments\\n", unpacked_path, packed_path, NSEGMENTS);')

    c.write("for (int t = 1; t <= NSEGMENTS; t++) free(masks[t]);")
    c.write("free(binary);")
    c.write("free(secret);")
    c.write("return 0;")
    c.dedent()
    c.write("}")


def write_secret_input(pack_name: str, nsegments: int):
    with open(f"secret_input_{pack_name}", "wb") as f:
        for _ in range(2 * nsegments):
            f.write(bytes([random.getrandbits(8)]))


def write_generated_sources(pack_name: str, nsegments: int, flag: str):
    global SHA_LOOP_LABEL_COUNTER, KEYSCHED_LABEL_COUNTER, TARGET_LOOP_LABEL_COUNTER, POOL_MUT_LABEL_COUNTER, STREAM_PASS_LABEL_COUNTER
    SHA_LOOP_LABEL_COUNTER = 0
    KEYSCHED_LABEL_COUNTER = 0
    TARGET_LOOP_LABEL_COUNTER = 0
    POOL_MUT_LABEL_COUNTER = 0
    STREAM_PASS_LABEL_COUNTER = 0

    specs = make_segment_specs(nsegments)
    sha_init0 = random_sha_init_bytes()
    sha_init1 = random_sha_init_bytes()

    runtime = CodeWriter()
    emit_runtime_c(runtime, nsegments, flag, sha_init0, sha_init1, specs)
    runtime.save(f"generated_code_{pack_name}.c")

    c = CodeWriter()
    emit_encryptor_c(c, pack_name, nsegments, sha_init0, sha_init1, specs)
    c.save(f"generated_encrypt_{pack_name}.c")


def main():
    if len(sys.argv) < 2:
        raise RuntimeError("Usage: python3 generate.py <pack_name>")
    pack_name = sys.argv[1]
    nsegments = int(os.getenv("NSEGMENTS", "256"))

    flag = open(f"flag_{pack_name}").read().strip()

    write_generated_sources(pack_name, nsegments, flag)
    write_secret_input(pack_name, nsegments)


if __name__ == "__main__":
    main()
