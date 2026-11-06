import itertools
import random
import re

SCALE = 1000
MIN_FACTOR = 180
MAX_RITES = 12

TYPE_FOCUS = 1
TYPE_INVOKE = 2
TYPE_DRAW = 3
TYPE_CARVE = 4
TYPE_MERGE = 5
TYPE_BLESS = 6
TYPE_GATE = 7
TYPE_SPARK = 8

base_cost = [0, 12, 10, 8, 7, 5, 4, 3, 2]
variant_weight = [860, 900, 940, 980, 1010, 1040, 1070, 1100, 930, 970, 1000, 1030, 1060, 1090, 1120, 1160]
operand_weight = [72, 84, 96, 108, 66, 78, 90, 102, 114, 126, 138, 150, 70, 82, 94, 106]
primary_bias = [-12, -8, 10, 6, 3, -2, -4, 9, -7, 4, 11, -3, 2, -5, 5, -1]
secondary_bias = [-7, 5, 4, -3, 2, 1, -4, 6, -2, 3, 8, -1, 0, -5, 7, -6]
primary_reduction = [248, 180, 240, 170, 130, 200, 172, 120, 142, 212, 162, 166, 152, 111, 220, 176]
secondary_reduction = [82, 110, 0, 102, 72, 86, 121, 92, 94, 0, 131, 84, 100, 106, 151, 116]
rites = [
    (TYPE_FOCUS,  TYPE_SPARK, 0x04A4, 0x9081),
    (TYPE_DRAW,   TYPE_MERGE, 0x120C, 0x0222),
    (TYPE_INVOKE, 0,          0x2082, 0x0000),
    (TYPE_CARVE,  TYPE_BLESS, 0x4408, 0x8140),
    (TYPE_GATE,   TYPE_MERGE, 0x9006, 0x0188),
    (TYPE_FOCUS,  TYPE_BLESS, 0x0484, 0x4220),
    (TYPE_INVOKE, TYPE_DRAW,  0x0428, 0x1840),
    (TYPE_MERGE,  TYPE_SPARK, 0x8100, 0x2090),
    (TYPE_CARVE,  TYPE_GATE,  0x5010, 0x1024),
    (TYPE_BLESS,  0,          0x2440, 0x0000),
    (TYPE_DRAW,   TYPE_FOCUS, 0x0C80, 0x8811),
    (TYPE_INVOKE, TYPE_GATE,  0x4009, 0x2003),
    (TYPE_MERGE,  TYPE_BLESS, 0x0242, 0x1280),
    (TYPE_SPARK,  TYPE_CARVE, 0x9410, 0x2048),
    (TYPE_FOCUS,  TYPE_INVOKE,0x08A0, 0x0441),
    (TYPE_DRAW,   TYPE_MERGE, 0x4210, 0x4012),
]

text = open("generated_chamber.h", "r", encoding="ascii").read()
nums = re.findall(r"0x([0-9a-fA-F]{2})", text)
blob = [int(x, 16) for x in nums]
assert len(blob) == 2736

def rite_reduction(rite_id, typ, var):
    pri, sec, pm, sm = rites[rite_id]
    red = 0
    if typ == pri:
        red = primary_reduction[rite_id] + primary_bias[var] + (22 if (pm & (1 << var)) else 0)
    elif sec and typ == sec:
        red = secondary_reduction[rite_id] + secondary_bias[var] + (16 if (sm & (1 << var)) else 0)
    if red < 0:
        red = 0
    if red > 460:
        red = 460
    return red

def apply_interactions(order, typ, var, factor):
    pos = [255] * 16
    for i, r in enumerate(order):
        pos[r] = i
    if pos[0] != 255 and pos[5] != 255 and pos[0] < pos[5] and typ == TYPE_FOCUS and var in (2, 7, 10):
        factor = factor * 860 // SCALE
    if pos[1] != 255 and pos[15] != 255 and pos[1] < pos[15] and typ == TYPE_MERGE and var in (1, 9):
        factor = factor * 900 // SCALE
    if pos[2] != 255 and pos[6] != 255 and pos[2] < pos[6] and typ == TYPE_INVOKE:
        factor = factor * 1080 // SCALE
    if pos[3] != 255 and pos[8] != 255 and pos[3] < pos[8] and typ == TYPE_CARVE:
        factor = factor * 1060 // SCALE
    if pos[12] != 255 and pos[7] != 255 and pos[12] < pos[7] and typ == TYPE_MERGE and var in (2, 9, 11):
        factor = factor * 1070 // SCALE
    if pos[1] != 255 and pos[15] != 255 and pos[12] != 255 and pos[1] < pos[15] < pos[12] and typ == TYPE_MERGE and var in (1, 9):
        factor = factor * 780 // SCALE
    if pos[0] != 255 and pos[5] != 255 and pos[14] != 255 and pos[0] < pos[5] < pos[14] and typ == TYPE_FOCUS and var in (2, 7, 10):
        factor = factor * 800 // SCALE
    if pos[4] != 255 and pos[7] != 255 and pos[9] != 255 and pos[4] < pos[7] < pos[9] and typ == TYPE_GATE and var in (3, 6, 12):
        factor = factor * 710 // SCALE
    elif typ == TYPE_GATE and pos[4] != 255 and pos[7] != 255 and pos[4] < pos[7] and pos[9] == 255:
        factor = factor * 1060 // SCALE
    if factor < MIN_FACTOR:
        factor = MIN_FACTOR
    if factor > SCALE:
        factor = SCALE
    return factor

def score(order):
    total = 0
    for i in range(0, len(blob), 3):
        op = blob[i]
        a = blob[i + 1]
        b = blob[i + 2]
        typ = op >> 4
        var = op & 0xF
        factor = SCALE
        for r in order:
            red = rite_reduction(r, typ, var)
            if red:
                factor = factor * (SCALE - red) // SCALE
        factor = apply_interactions(order, typ, var, factor)
        w = base_cost[typ] * variant_weight[var]
        w += operand_weight[(a ^ b) & 0xF]
        w += ((a & 3) + (b & 3)) * 7
        total += w * factor // SCALE
    return total

BASELINE = score([])
TARGET = 3415200

# show that random inputs are very bad
for _ in range(10):
    order = random.sample(range(16), random.randint(8, 12))
    v = score(order)
    print(f"random {order} -> {v} (x{v / BASELINE:.3f})")

def greedy_init():
    chosen = []
    rem = set(range(16))
    cur = score(chosen)
    for _ in range(MAX_RITES):
        best = None
        best_v = cur
        for p in rem:
            cand = chosen + [p]
            v = score(cand)
            if v < best_v:
                best_v = v
                best = p
        if best is None:
            break
        chosen.append(best)
        rem.remove(best)
        cur = best_v
    return chosen


def local_search(chosen):
    chosen = chosen[:]
    while True:
        improved = False
        pool = [x for x in range(16) if x not in chosen]
        base = score(chosen)
        for i in range(len(chosen)):
            for p in pool:
                cand = chosen[:]
                cand[i] = p
                v = score(cand)
                if v < base:
                    chosen = cand
                    improved = True
                    break
            if improved:
                break
        if improved:
            continue
        for i, j in itertools.combinations(range(len(chosen)), 2):
            for p, q in itertools.permutations(pool, 2):
                cand = chosen[:]
                cand[i], cand[j] = p, q
                v = score(cand)
                if v < base:
                    chosen = cand
                    improved = True
                    break
            if improved:
                break
        if not improved:
            return chosen


def search_order(chosen, trials=3000):
    best = chosen[:]
    best_v = score(best)
    for _ in range(trials):
        cand = random.sample(chosen, len(chosen))
        v = score(cand)
        if v < best_v:
            best, best_v = cand, v
    return best, best_v

seed = greedy_init()
greedy_v = score(seed)
seed = local_search(seed)
best, best_v = search_order(seed)
print(seed, greedy_v, best, best_v, TARGET)

while best_v > TARGET:
    cand = random.sample(range(16), random.randint(8, 12))
    cand = local_search(cand)
    cand, v = search_order(cand, 2000)
    if v < best_v:
        print(f"improved {best_v} -> {v} with {cand}")
        best, best_v = cand, v

enc = "".join(f"{r:x}{i:x}" for i, r in enumerate(best))
print(f"baseline={BASELINE}")
print(f"target={TARGET}")
print(f"greedy={greedy_v}")
print(f"best={best_v}")
print(f"len={len(best)}")
print(f"order={best}")
print(f"hex={enc}")
print("pass" if best_v <= TARGET else "fail")
