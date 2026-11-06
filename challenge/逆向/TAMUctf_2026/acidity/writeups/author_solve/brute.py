import ctypes

uint64 = ctypes.c_uint64

def clock_prng(state, input):
    # Replicate the custom_random function from game.cpp
    mix = uint64(input).value
    mix |= mix << 32

    state = uint64(state).value
    state ^= mix
    state = uint64(state).value
    state ^= state << 12
    state = uint64(state).value
    state ^= state >> 25
    state = uint64(state).value
    state ^= state << 27
    return uint64(state * 0xF337).value, uint64(state).value

def check_good(bits):
    return (bits >> 17) & 1

alpha = b'bcefghijklmnopqrstuvwxyz0123456789BCEFGHIJKLMNOPQRSTUVWXYZ{}_!'

def dfs(state, path):
    if len(path) == 14:
        # valid solution found
        print("Found solution:", path)
        return path
    
    for c in alpha:
        rand_val, next_state = clock_prng(state, c)
        if check_good(rand_val):
            if (result := dfs(next_state, path + [(c, next_state)])):
                return result
            
    return False

initial_state = 0xF10C70DEADBEEF00
path = dfs(initial_state, [])
inp = bytes([c for c, _ in path])
states = [s for _, s in path]
print("Input:", inp)
print("States:", [hex(s) for s in states])

for i in range(1, len(inp)):
    prev_state = states[i - 1]
    c = inp[i]
    rand_val, next_state = clock_prng(prev_state, c)
    assert next_state == states[i]
    assert check_good(rand_val)