import itertools
import random
import re
import math
import sys

# --- CONSTANTS ---
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

# --- LOAD BLOB ---
print("Loading and parsing generated_chamber.h...")
try:
    text = open("generated_chamber.h", "r", encoding="ascii").read()
    nums = re.findall(r"0x([0-9a-fA-F]{2})", text)
    blob = [int(x, 16) for x in nums]
    assert len(blob) == 2736
except Exception as e:
    print(f"Error loading generated_chamber.h: {e}")
    sys.exit(1)

# --- EVALUATION PRE-COMPUTATION ---
def build_score_context():
    instructions = []
    for i in range(0, len(blob), 3):
        op = blob[i]
        a = blob[i + 1]
        b = blob[i + 2]
        typ = op >> 4
        var = op & 0xF
        w = base_cost[typ] * variant_weight[var]
        w += operand_weight[(a ^ b) & 0xF]
        w += ((a & 3) + (b & 3)) * 7
        instructions.append((typ, var, w))

    grouped = {}
    for typ, var, w in instructions:
        grouped.setdefault((typ, var), []).append(w)

    red_matrix = {}
    for r in range(16):
        red_matrix[r] = {}
        pri, sec, pm, sm = rites[r]
        for typ in range(9):
            for var in range(16):
                red = 0
                if typ == pri:
                    red = primary_reduction[r] + primary_bias[var] + (22 if (pm & (1 << var)) else 0)
                elif sec and typ == sec:
                    red = secondary_reduction[r] + secondary_bias[var] + (16 if (sm & (1 << var)) else 0)
                
                if red < 0: red = 0
                if red > 460: red = 460
                if red > 0:
                    red_matrix[r][(typ, var)] = SCALE - red

    return grouped, red_matrix

GROUPED, RED_MATRIX = build_score_context()

# --- FAST SCORING FUNCTION ---
def score(order):
    pos = [255] * 16
    for i, r in enumerate(order):
        pos[r] = i

    # Compute sequence conditions once
    c_f2 = pos[0] != 255 and pos[5] != 255 and pos[0] < pos[5]
    c_m2 = pos[1] != 255 and pos[15] != 255 and pos[1] < pos[15]
    c_i = pos[2] != 255 and pos[6] != 255 and pos[2] < pos[6]
    c_c = pos[3] != 255 and pos[8] != 255 and pos[3] < pos[8]
    c_mbad = pos[12] != 255 and pos[7] != 255 and pos[12] < pos[7]
    c_m3 = pos[1] != 255 and pos[15] != 255 and pos[12] != 255 and pos[1] < pos[15] < pos[12]
    c_f3 = pos[0] != 255 and pos[5] != 255 and pos[14] != 255 and pos[0] < pos[5] < pos[14]
    c_g3 = pos[4] != 255 and pos[7] != 255 and pos[9] != 255 and pos[4] < pos[7] < pos[9]
    c_gbad = pos[4] != 255 and pos[7] != 255 and pos[4] < pos[7] and pos[9] == 255

    total = 0
    for (typ, var), ws in GROUPED.items():
        factor = SCALE
        for r in order:
            m = RED_MATRIX[r].get((typ, var))
            if m:
                factor = factor * m // SCALE

        # Sequential cascade checks
        if c_f2 and typ == TYPE_FOCUS and var in (2, 7, 10): factor = factor * 860 // SCALE
        if c_m2 and typ == TYPE_MERGE and var in (1, 9): factor = factor * 900 // SCALE
        if c_i and typ == TYPE_INVOKE: factor = factor * 1080 // SCALE
        if c_c and typ == TYPE_CARVE: factor = factor * 1060 // SCALE
        if c_mbad and typ == TYPE_MERGE and var in (2, 9, 11): factor = factor * 1070 // SCALE
        if c_m3 and typ == TYPE_MERGE and var in (1, 9): factor = factor * 780 // SCALE
        if c_f3 and typ == TYPE_FOCUS and var in (2, 7, 10): factor = factor * 800 // SCALE
        if typ == TYPE_GATE:
            if c_g3 and var in (3, 6, 12): factor = factor * 710 // SCALE
            elif c_gbad: factor = factor * 1060 // SCALE

        if factor < MIN_FACTOR: factor = MIN_FACTOR
        if factor > SCALE: factor = SCALE

        for w in ws:
            total += w * factor // SCALE

    return total

TARGET = 3415150

# --- INITIALIZATION ---
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
        if best is None: break
        chosen.append(best)
        rem.remove(best)
        cur = best_v
    return chosen

# --- SIMULATED ANNEALING ---
def simulated_annealing(initial_seq, target_score, initial_temp=10000.0, cooling_rate=0.9995, max_iter=50000):
    current_seq = initial_seq[:]
    current_score = score(current_seq)
    
    best_seq = current_seq[:]
    best_score = current_score
    
    temp = initial_temp
    
    for i in range(max_iter):
        neighbor = current_seq[:]
        op = random.random()
        
        # 1. Swap two random elements
        if op < 0.4 and len(neighbor) > 1:
            idx1, idx2 = random.sample(range(len(neighbor)), 2)
            neighbor[idx1], neighbor[idx2] = neighbor[idx2], neighbor[idx1]
            
        # 2. Extract an element and insert it elsewhere
        elif op < 0.8 and len(neighbor) > 1:
            idx1, idx2 = random.sample(range(len(neighbor)), 2)
            val = neighbor.pop(idx1)
            neighbor.insert(idx2, val)
            
        # 3. Mutate an element completely
        else:
            pool = [x for x in range(16) if x not in neighbor]
            if pool:
                idx = random.randrange(len(neighbor))
                neighbor[idx] = random.choice(pool)

        neighbor_score = score(neighbor)
        delta = neighbor_score - current_score
        
        if delta < 0:
            current_seq = neighbor
            current_score = neighbor_score
            if current_score < best_score:
                print(f"New best score: {current_score} | Order: {current_seq}")
                best_seq = current_seq[:]
                best_score = current_score
                if best_score <= target_score:
                    return best_seq, best_score
        else:
            # Randomly accept worse moves depending on the current temperature
            acceptance_probability = math.exp(-delta / temp)
            if random.random() < acceptance_probability:
                current_seq = neighbor
                current_score = neighbor_score
                
        temp *= cooling_rate
        if temp < 0.0001:
            break
            
    return best_seq, best_score

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print(f"Target:   {TARGET}")
    
    seed = greedy_init()
    print(f"Greedy Init Score: {score(seed)} | Order: {seed}")
    print("Starting Simulated Annealing...")
    
    # Initial SA run using the greedy seed
    best, best_v = simulated_annealing(seed, TARGET)

    restarts = 0
    while best_v > TARGET:
        restarts += 1
        print(f"Restarting Annealing ({restarts})... Current best is {best_v}")
        random_seed = random.sample(range(16), random.randint(8, 12))
        cand, v = simulated_annealing(random_seed, TARGET, initial_temp=5000.0)
        
        if v < best_v:
            best, best_v = cand, v
            print(f"--> Found new minimum: {best_v}")

    enc = "".join(f"{r:x}{i:x}" for i, r in enumerate(best))
    
    print("\n" + "=" * 30)
    print("RESULTS:")
    print("=" * 30)
    print(f"target={TARGET}")
    print(f"best={best_v}")
    print(f"len={len(best)}")
    print(f"order={best}")
    print(f"hex={enc}")
    print("pass" if best_v <= TARGET else "fail")