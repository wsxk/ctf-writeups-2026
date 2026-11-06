import os
import zipfile
import json
import random
import string
import copy
import math

from tqdm import tqdm

project = json.load(open('cleaned.json'))

START = 'l'
END = 'd'
blocks = project['targets'][1]['blocks']

visited = set()
tree = {START: []}
def get_tree(cur):
    visited.add(cur)
    for block_id in blocks:
        if block_id in visited or block_id == cur or block_id == END:
            continue
        if 'parent' in blocks[block_id] and blocks[block_id]['parent'] == cur:
            if cur not in tree:
                tree[cur] = []
            tree[cur].append((block_id, blocks[block_id]
                             ['opcode'], blocks[block_id]['inputs']))
            if block_id not in visited:
                get_tree(block_id)
get_tree(START)

alpha = string.ascii_letters + string.punctuation[7:-5]
def rand_str(n):
    return ''.join(random.choices(alpha, k=n))


_USED_IDS = set()
def gen_id(n=12):
    global _USED_IDS
    while True:
        new_id = rand_str(n)
        if new_id not in _USED_IDS:
            _USED_IDS.add(new_id)
            return new_id


# remember to set parent yourself
def make_block(op=None, inputs={}, fields={}):
    block = {
        "opcode": op,
        "next": None,
        "parent": None,
        "inputs": {},
        "fields": {},
        "shadow": False,
        "topLevel": False
    }

    for k, v in inputs.items():
        if isinstance(v, str):
            # if v is in used ids, its a block input (3), otherwise its a string (10)
            if v in _USED_IDS:
                block["inputs"][k] = [3, v]
            else:
                block["inputs"][k] = [1, [10, v]]
        else:
            # all nums are type 4
            block["inputs"][k] = [1, [4, str(v)]]

    for k, v in fields.items():
        block["fields"][k] = [v, None]

    return gen_id(), block


def make_mathop(op, arg):
    return make_block(op="operator_mathop", inputs={"NUM": arg}, fields={"OPERATOR": op})


def make_operator(op, args):
    one_op_num = [
        "round"
    ]
    one_op_str = [
        "length"
    ]
    two_op_num = [
        "add", "multiply", "subtract", "divide", "mod"
    ]
    two_op_str = [
        "join"
    ]
    two_op_op = [
        "gt", "lt", "equals"
    ]
    if op in one_op_num:
        return make_block(op=f"operator_{op}", inputs={"NUM": args[0]})
    elif op in one_op_str:
        return make_block(op=f"operator_{op}", inputs={"STRING": args[0]})
    elif op in two_op_num:
        return make_block(op=f"operator_{op}", inputs={"NUM1": args[0], "NUM2": args[1]})
    elif op in two_op_str:
        return make_block(op=f"operator_{op}", inputs={"STRING1": args[0], "STRING2": args[1]})
    elif op in two_op_op:
        return make_block(op=f"operator_{op}", inputs={"OPERAND1": args[0], "OPERAND2": args[1]})
    else:
        raise ValueError(f"Unknown operator {op}")


_BAG = []
def gen_const(n):
    # create series of ops + root id that evaluates to some constant n
    global _BAG
    const_ops = {}

    if n == 0:
        r = random.randint(1, 5)
    else:
        r = random.randint(1, 6)
        # because why true randomness
        while r in _BAG:
            r = random.randint(1, 6)
        _BAG.append(r)
        if len(_BAG) >= 3:
            _BAG = []

    match r:
        case 1:
            # n = floor(sqrt(e^(tan(k))))
            n_ = n + random.random() / 4
            k = math.atan(math.log(n_ ** 2))
            _k = math.degrees(k)  # actually use degrees in block
            # print(n, _k, math.floor(math.sqrt(math.exp(math.tan(k)))))
            assert math.floor(math.sqrt(math.exp(math.tan(k)))) == n

            tan_id, tan = make_mathop("tan", _k)
            exp_id, exp = make_mathop("e ^", tan_id)
            sqrt_id, sqrt = make_mathop("sqrt", exp_id)
            floor_id, floor = make_mathop("floor", sqrt_id)
            tan['parent'] = exp_id
            exp['parent'] = sqrt_id
            sqrt['parent'] = floor_id
            const_ops[tan_id] = tan
            const_ops[exp_id] = exp
            const_ops[sqrt_id] = sqrt
            const_ops[floor_id] = floor
            return floor_id, const_ops

        case 2:
            # n = round(k * (10^(ln(len(x / (a > b)))))) -> a < b -> x / 0 = Infinity
            # n = round(k * (10^(ln(8))))
            x, b = random.random(), random.randint(2, 10**4)
            a = random.randint(1, b - 1)
            k = n / (10 ** math.log(8))
            assert round(k * (10 ** math.log(8))) == n

            gt_id, gt = make_operator("gt", [a, b])
            div_id, div = make_operator("divide", [x, gt_id])
            length_id, length = make_operator("length", [div_id])
            ln_id, ln = make_mathop("ln", length_id)
            pow_id, pow_ = make_mathop("10 ^", ln_id)
            mul_id, mul = make_operator("multiply", [k, pow_id])
            round_id, round_ = make_operator("round", [mul_id])
            gt['parent'] = div_id
            div['parent'] = length_id
            length['parent'] = ln_id
            ln['parent'] = pow_id
            pow_['parent'] = mul_id
            mul['parent'] = round_id
            const_ops[gt_id] = gt
            const_ops[div_id] = div
            const_ops[length_id] = length
            const_ops[ln_id] = ln
            const_ops[pow_id] = pow_
            const_ops[mul_id] = mul
            const_ops[round_id] = round_
            return round_id, const_ops

        case 3:
            # n = (a - b) + (c - d)
            # where a, b, c, d very big
            a = random.randint(10**6, 10**7)
            b = random.randint(10**6, 10**7)
            c = random.randint(10**6, 10**7)
            d = a - b + c - n
            # print(n, a, b, c, d, (a - b) + (c - d))
            assert (a - b) + (c - d) == n

            sub1_id, sub1 = make_operator("subtract", [a, b])
            sub2_id, sub2 = make_operator("subtract", [c, d])
            add_id, add = make_operator("add", [sub1_id, sub2_id])
            sub1['parent'] = add_id
            sub2['parent'] = add_id
            const_ops[sub1_id] = sub1
            const_ops[sub2_id] = sub2
            const_ops[add_id] = add
            return add_id, const_ops

        case 4:
            # n = (x + y) % (a * (b - c))
            a = random.randint(10**2, 10**3)
            b = random.randint(10**2, 10**3)
            c = random.randint(1, b - 1)
            m = a * (b - c)
            while m <= n:
                a = random.randint(10**2, 10**3)
                b = random.randint(10**2, 10**3)
                c = random.randint(1, b - 1)
                m = a * (b - c)
            x = random.randint(1, m) + m * random.randint(1, 5)
            y = (n - x) % m + m * random.randint(1, 5)
            assert (x + y) % (a * (b - c)) == n

            add_id, add = make_operator("add", [x, y])
            sub_id, sub = make_operator("subtract", [b, c])
            mul_id, mul = make_operator("multiply", [a, sub_id])
            mod_id, mod = make_operator("mod", [add_id, mul_id])
            add['parent'] = mod_id
            sub['parent'] = mul_id
            mul['parent'] = mod_id
            const_ops[add_id] = add
            const_ops[sub_id] = sub
            const_ops[mul_id] = mul
            const_ops[mod_id] = mod
            return mod_id, const_ops

        case 5:
            # n = (len(join(a, b)) * len(join(c, d))) + e
            a = rand_str(random.randint(1, 10))
            b = rand_str(random.randint(1, 10))
            c = rand_str(random.randint(1, 10))
            d = rand_str(random.randint(1, 10))
            e = n - (len(a) + len(b)) * (len(c) + len(d))
            # print(n, a, b, c, d, e, (len(a) + len(b)) * (len(c) + len(d)) + e)
            assert (len(a) + len(b)) * (len(c) + len(d)) + e == n

            join1_id, join1 = make_operator("join", [a, b])
            join2_id, join2 = make_operator("join", [c, d])
            length1_id, length1 = make_operator("length", [join1_id])
            length2_id, length2 = make_operator("length", [join2_id])
            mul_id, mul = make_operator("multiply", [length1_id, length2_id])
            add_id, add = make_operator("add", [mul_id, e])
            join1['parent'] = length1_id
            join2['parent'] = length2_id
            length1['parent'] = mul_id
            length2['parent'] = mul_id
            mul['parent'] = add_id
            const_ops[join1_id] = join1
            const_ops[join2_id] = join2
            const_ops[length1_id] = length1
            const_ops[length2_id] = length2
            const_ops[mul_id] = mul
            const_ops[add_id] = add
            return add_id, const_ops

        case _:
            # n = q * d + r
            q = random.randint(1, n)
            d, r = divmod(n, q)
            assert q * d + r == n

            mul_id, mul = make_operator("multiply", [q, d])
            add_id, add = make_operator("add", [mul_id, r])
            mul['parent'] = add_id
            const_ops[mul_id] = mul
            const_ops[add_id] = add
            return add_id, const_ops


base_keys = set(tree.keys())
eqs_data = open('eqs.txt').read().splitlines()
eqs_data = [line for line in eqs_data if line.strip() != '']
N = len(eqs_data)

START = 'l'
END = 'd'
LIST_FIELD = {
    "LIST": [
        "enwrap 330 times in long swaths of frozen blood",
        "Ob7NZ-wVNV~SOQ26}pkG"
    ]
}
VAR_FIELD = {
    "VARIABLE": [
        "goodbye now, a sorrow in you",
        "4e6L`senD5|svVe6R3Pp"
    ]
}
def gen_ops(idx, eq):
    a, b, c, target = eq
    a_id, a_ = gen_const(a)
    b_id, b_ = gen_const(b)
    c_id, c_ = gen_const(c)
    target_id, target_ = gen_const(target)
    prev_idx_id, prev_idx = gen_const((idx - 1) % N + 1)
    curr_idx_id, curr_idx = gen_const(idx % N + 1)
    next_idx_id, next_idx = gen_const((idx + 1) % N + 1)

    prev_item_id, prev_item = make_block(op="data_itemoflist", inputs={"INDEX": prev_idx_id})
    curr_item_id, curr_item = make_block(op="data_itemoflist", inputs={"INDEX": curr_idx_id})
    next_item_id, next_item = make_block(op="data_itemoflist", inputs={"INDEX": next_idx_id})
    for item in [prev_item, curr_item, next_item]:
        item['fields'] = LIST_FIELD
    prev_idx[prev_idx_id]['parent'] = prev_item_id
    curr_idx[curr_idx_id]['parent'] = curr_item_id
    next_idx[next_idx_id]['parent'] = next_item_id

    a_mul_id, a_mul = make_operator("multiply", [a_id, prev_item_id])
    a_[a_id]['parent'] = a_mul_id
    prev_item['parent'] = a_mul_id
    b_mul_id, b_mul = make_operator("multiply", [b_id, curr_item_id])
    b_[b_id]['parent'] = b_mul_id
    curr_item['parent'] = b_mul_id
    c_mul_id, c_mul = make_operator("multiply", [c_id, next_item_id])
    c_[c_id]['parent'] = c_mul_id
    next_item['parent'] = c_mul_id

    add1_id, add1 = make_operator("add", [a_mul_id, b_mul_id])
    a_mul['parent'] = add1_id
    b_mul['parent'] = add1_id
    add2_id, add2 = make_operator("add", [add1_id, c_mul_id])
    add1['parent'] = add2_id
    c_mul['parent'] = add2_id
    sub_id, sub = make_operator("subtract", [add2_id, target_id])
    add2['parent'] = sub_id
    target_[target_id]['parent'] = sub_id

    abs_id, abs_ = make_mathop("abs", sub_id)
    sub['parent'] = abs_id

    root_id, root = make_block(op="data_changevariableby", inputs={"VALUE": abs_id})
    abs_['parent'] = root_id
    root['fields'] = VAR_FIELD

    block_ops = {
        prev_item_id: prev_item,
        curr_item_id: curr_item,
        next_item_id: next_item,
        a_mul_id: a_mul,
        b_mul_id: b_mul,
        c_mul_id: c_mul,
        add1_id: add1,
        add2_id: add2,
        sub_id: sub,
        abs_id: abs_,
        root_id: root
    }
    block_ops.update(a_)
    block_ops.update(b_)
    block_ops.update(c_)
    block_ops.update(target_)
    block_ops.update(prev_idx)
    block_ops.update(curr_idx)
    block_ops.update(next_idx)
    return block_ops, root_id

all_ops = []
for i, line in list(enumerate(tqdm(eqs_data[:1000])))[1:]:
# for i, line in enumerate(tqdm(eqs_data)):
    eq = tuple(map(int, line.split()))
    ops, root = gen_ops(i, eq)
    all_ops.append((ops, root))
random.shuffle(all_ops)

prev = START
for ops, root in all_ops:
    blocks.update(ops)
    blocks[prev]['next'] = root
    blocks[root]['parent'] = prev
    prev = root

# clean up end
blocks[prev]['next'] = END
blocks[END]['parent'] = prev

# clean up start
start_prev = blocks[START]['parent']
blocks[all_ops[0][1]]['parent'] = start_prev
blocks[start_prev]['next'] = all_ops[0][1]
del blocks[START]

# low constants go byebye
replace_consts = [0, 1, 2, 3, 4, 256, 65536]
for _ in range(1):
    for block in tqdm(list(blocks.keys())):
        for value_field in ["VALUE", "NUM", "NUM1", "NUM2", "OPERAND1", "OPERAND2", "TIMES"]:
            if value_field in blocks[block]['inputs'] and blocks[block]['inputs'][value_field][0] == 1:
                value = blocks[block]['inputs'][value_field][1]
                if value[0] == 4 and '.' not in value[1] and int(value[1]) in replace_consts:
                    const_val = int(value[1])
                    const_id, const_blocks = gen_const(const_val)
                    blocks.update(const_blocks)
                    blocks[const_id]['parent'] = block
                    blocks[block]['inputs'][value_field] = [3, const_id]

                # also check string
                elif value[0] == 10:
                    try:
                        int_value = int(value[1])
                        if int_value in replace_consts:
                            const_val = int_value
                            const_id, const_blocks = gen_const(const_val)
                            blocks.update(const_blocks)
                            blocks[const_id]['parent'] = block
                            blocks[block]['inputs'][value_field] = [
                                3, const_id]
                    except:
                        pass

                # repeat
                elif value_field == 'TIMES' and value[0] == 6:
                    int_value = int(value[1])
                    if int_value in replace_consts:
                        const_val = int_value
                        const_id, const_blocks = gen_const(const_val)
                        blocks.update(const_blocks)
                        blocks[const_id]['parent'] = block
                        blocks[block]['inputs'][value_field] = [3, const_id]

print(f"total blocks: {len(blocks)}")
print("dumping json...")
open('skretch/project.json', 'w').write(json.dumps(project))

print("zipping...")
with zipfile.ZipFile('skretch.zip', 'w') as zipf:
    for foldername, subfolders, filenames in os.walk('skretch'):
        for filename in filenames:
            file_path = os.path.join(foldername, filename)
            zipf.write(file_path, os.path.relpath(file_path, 'skretch'))

os.rename('skretch.zip', 'skretch.sb3')
