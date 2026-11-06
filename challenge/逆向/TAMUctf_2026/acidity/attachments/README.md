# acidity

Author: `flocto`

Make sure you brought your helmet.

## Solution

I don't really have a writeup for the main rev part, but you can actually ignore most of it once you find the PRNG and simplify it out.

Then it's just a matter of doing DFS / brute force to get a good input for each "rain" tick. Since you can send any byte, and the result is only the value of a single bit, there are lots of possible inputs that will work.

```c
static uint64_t rng_state = 0xF10C70DEADBEEF00ULL;
static uint64_t __attribute__((noinline)) custom_random(int input) {
    uint64_t mix = static_cast<uint64_t>(input);
    mix |= mix << 32;

    rng_state ^= mix;
    rng_state ^= rng_state << 12;
    rng_state ^= rng_state >> 25;
    rng_state ^= rng_state << 27;
    return rng_state * 0xF337ULL;
}
```

From here, the rest is just careful manipulation of the player so that they move out of the way of the first rain drops, then drop back down to the flag before the timer runs out.

See either solve directory for scripts that do this.

flag:
`gigem{RNG_m4nipul4t10n_ftw..._0r_ju5t_br1n6_4_sh0v3l}`
