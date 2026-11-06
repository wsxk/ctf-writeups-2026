# IT'S ME, BURHAN!

**Category:** Reverse Engineering · **Points:** 500 · **Solves at capture:** 1 · **Flag:** `COMPFEST18{bUR_BuR_BUr_buRh4n_h4Un7s_m3_t!L_t0D4y_QsUqWOYSImTdtQ9B}`

---

## Challenge Description

> The Adventurers' Guild of Eisenwald runs on an old terminal program, BurhanQuest (a Java .jar).
> Guildmaster Burhan keeps secrets behind his admin account and insists his password
> "lives in the guild itself, for those who look closely enough."
> You get a wanderer account (`frieren`/`frieren`) and a copy of the program.
> Get in, look closely, and recover what he's hiding.

We're handed `burhanquest.jar` and a remote terminal to connect to. The goal is to log in as `burhan` and retrieve an encrypted flag from the admin menu.

---

## Initial Analysis

### Unpacking the JAR

A `.jar` file is just a ZIP archive of compiled Java `.class` files, so standard Java reversing tools work fine:

```bash
jar tf burhanquest.jar        # list contents
javap -classpath burhanquest.jar -c -p l > l.javap
javap -classpath burhanquest.jar -c -p p > p.javap
jadx -d jadx-output burhanquest.jar   # readable decompiled source
```

`jadx` — a popular Java decompiler — gives us reconstructed source that is easier to read than raw bytecode, even if the output is imperfect. The result revealed two classes that do all the heavy lifting:

- **`l`** — holds the seeded guild configuration, the generated admin password data, and the encrypted flag.
- **`p`** — utility class: SHA-256 hashing, byte/integer conversions, permutation unranking, all 18 reversible transformations, and the alphabet table.

Almost every identifier had been reduced to a single letter by an obfuscator, and constants were XOR-encoded so they wouldn't appear literally in the binary. That said, the *data flow* was still visible in the bytecode, which is what matters.

### The account model

The server hands each fresh connection a seeded guild instance — random parameters such as Frieren's starting level and coin count, quest coin rewards, and the three quests Burhan "requires." Logging in as `frieren`/`frieren` drops us into a terminal menu with options for profile, quest list, battle, archive, export, and more.

The admin (`burhan`) menu has option 13: "Print sealed archive." That sealed archive is the flag, encrypted by the same transformation engine used to produce Burhan's password — so we need the password before we can decrypt anything.

---

## The Vulnerability / Core Concept

The challenge description says the password "lives in the guild itself." That is completely literal.

Burhan's password is deterministically generated from nine values that the ordinary `frieren` account can observe through the guild's own menus:

| # | Value | Where to find it |
|---|-------|-----------------|
| 0 | Frieren's starting level | Profile menu |
| 1 | Frieren's starting coin count | Profile menu |
| 2 | Battle sigil after quest 1 | Battle result |
| 3 | Archive sigil after quest 1 | Archive menu |
| 4 | Battle sigil after quest 2 | Battle result |
| 5 | Export sigil after quest 2 | Export menu |
| 6 | Battle sigil after quest 3 | Battle result |
| 7 | Archive sigil after quest 3 | Archive menu |
| 8 | Final coin count (calculated) | Profile + quest rewards |

This is not a password cracking problem. There is no brute force. The password is recoverable by anyone who reads the menus carefully — hence "for those who look closely enough."

The trick is that **the three required quests are also derived deterministically** from the starting level and coins, and **the sigils are order-dependent** — archive and export sigils incorporate the current quest-completion history, so you must complete the quests in exactly the right order or collect the wrong values.

---

## Exploitation

The exploit has five phases.

### Phase 1 — Determine the three required quests

The JAR hashes the starting level and coin count to pick an ordered selection of three quests from the 18 available:

```text
route_seed = U64(SHA256(BE32(level) || BE32(coins))) mod 4896
route      = unrank_ordered_selection(route_seed, 18, 3)
```

`4896 = 18 × 17 × 16` is the total number of ordered 3-element selections from 18. `unrank_ordered_selection` — implemented in `p.a(long, int, int)` — converts a single integer into the corresponding ordered tuple. Rather than re-implementing it, `Solve.java` compiles against the challenge JAR and calls `p.a` directly:

```java
long routeSeed = p.b(sha(cat(p.a(level), p.a(coins)))) % 4896L;
int[] route = p.a(routeSeed, 18, 3);
```

For the final instance this produced `Q15 → Q10 → Q12`.

### Phase 2 — Collect the six sigils in order

With the route known, we work through the terminal menus in a specific sequence:

```
complete Q15  → save battle sigil (decimal integer)
open archive  → save archive sigil (hex string, must be hex-decoded before use)
complete Q10  → save battle sigil
export data   → save export sigil (hex string)
complete Q12  → save battle sigil
open archive  → save archive sigil again (it changed!)
```

For the final instance:

```
battle_p  = 63790
archive_p = 353630043dc3
battle_q  = 37293
export_q  = f7305349bb84
battle_r  = 17714
archive_r = 09025c019eb1
```

The final coin count is computed offline — initial coins plus the rewards for the three quests — to avoid reading the updated display value by mistake.

### Phase 3 — Derive the password

`Solve.java` concatenates the nine byte-encoded pieces, hashes them, and uses the hash to select nine transformations from the 18 available. It also derives a permutation of the nine pieces from a second hash:

```java
// Choose 9 operations out of 18 (ordered, no repetition)
long t = p.b(sha(joined)) % 17643225600L;
int[] operations = p.a(t, 18, 9);

// Choose a permutation of the 9 pieces
long orderSeed = p.b(sha(cat(p.a(coins), p.a(level)))) % 362880L;
int[] order = p.a(orderSeed, 9, 9);
```

`17643225600 = 18!/(18-9)!` and `362880 = 9!`. The transformed, reordered pieces are folded into a SHA-256 hash chain whose output is 16 five-bit indices into a 32-character alphabet. Call this `target`.

Recovering the password means starting from `target` and applying each operation's inverse in reverse order, then indexing into the alphabet.

### Phase 4 — Invert the 18 transformations

Each of the 18 operation types has a clean mathematical inverse. A few examples:

```java
// Op 10: prefix XOR   →   inverse: XOR each element with the previous output
answer[0] = target[0];
for (int i = 1; i < n; i++) answer[i] = target[i] ^ target[i - 1];

// Op 12: prefix sum mod 32   →   inverse: subtract the previous output
answer[0] = target[0];
for (int i = 1; i < n; i++) answer[i] = (target[i] - target[i - 1]) & 31;

// Op 9: multiply by 3 mod 32   →   inverse: multiply by 11 (since 3×11 ≡ 1 mod 32)
answer[i] = (target[i] * 11) & 31;
```

All 18 inverses are in `Solve.java`. Every one was verified by running `inverse(forward(random_array)) == random_array` before trusting it.

One important gotcha: the byte-array overload `p.a(int, byte[])` and the int-array overload `p.a(int, int[])` use **different operation numbering**. For example, int-op 10 is prefix XOR, but byte-op 9 is prefix XOR. `Solve.java` handles this with an explicit mapping table:

```java
int[] mapping = {0, 1, 2, 3, -1, 4, 6, 7, 8, 10, 11, 9, 14, 15, 16, 17, 13, 12};
unsigned = invert(mapping[kind], unsigned, 256);
```

Missing this would produce a wrong password every time.

### Phase 5 — Log in as Burhan and decrypt the flag

With the password in hand we log back in:

```
username: burhan
password: WL7V35WOFCP24T5V   (instance-specific)
```

Admin option 13 prints a hex-encoded "sealed archive." That ciphertext is the flag's UTF-8 bytes after the same nine byte-array operations were applied. Decryption is the inverse loop:

```java
byte[] clear = hexDecode(sealedArchive);
for (int i = operations.length - 1; i >= 0; i--)
    clear = invertBytes(operations[i], clear);
System.out.println(new String(clear, StandardCharsets.UTF_8));
```

### Putting it all together — `exploit.py`

The Python script automates the full terminal session. It uses a raw socket `Tube` class (no pwntools dependency) to talk to the remote server, calls `Solve.java` via `subprocess` for the math-heavy steps, and parses the menus with regex.

```python
# Phase 1: derive the quest route
phase1 = java_solve([level, coins, reward_csv])
route = re.search(r"route=(Q\d+),(Q\d+),(Q\d+)", phase1).groups()

# Phase 2: collect sigils in order
battle_p = take_quest(io, route[0])
archive_p = re.search(r"sigil-arsip: ([0-9a-f]+)", choose(io, 7)).group(1)
battle_q = take_quest(io, route[1])
export_q  = re.search(r"sigil-ekspor: ([0-9a-f]+)", choose(io, 6)).group(1)
battle_r = take_quest(io, route[2])
archive_r = re.search(r"sigil-arsip: ([0-9a-f]+)", choose(io, 7)).group(1)

# Phase 3+4: derive password
phase2 = java_solve([level, coins, reward_csv, battle_p, archive_p,
                     battle_q, export_q, battle_r, archive_r])
password = re.search(r"password=(\S+)", phase2).group(1)

# Phase 5: log in as burhan and decrypt
login(io, "burhan", password)
io.sendline("13")
# ... collect sealed archive, call java_solve with it appended ...
```

`LocalDump.java` was a debugging helper used during development: it uses Java reflection to read the private fields of the running `l` instance directly, which let us verify the internal state matched our calculations before committing to the full automation.

---

## Key Commands / Payloads

```bash
# Decompile the JAR
jadx -d jadx-output burhanquest.jar

# Dump bytecode for both key classes
javap -classpath burhanquest.jar -c -p l > l.javap
javap -classpath burhanquest.jar -c -p p > p.javap

# Compile the solver helper against the challenge JAR
javac -cp burhanquest.jar Solve.java

# Run the solver (phase 1: just the route)
java -cp "burhanquest.jar:." Solve 14 5775 \
  "reward1,...,reward18"

# Run the solver (phase 2: full password derivation)
java -cp "burhanquest.jar:." Solve 14 5775 \
  "reward1,...,reward18" \
  63790 353630043dc3 37293 f7305349bb84 17714 09025c019eb1

# Full automation
python3 exploit.py YOUR_CTFD_TOKEN
```

---

## Flag

```
COMPFEST18{bUR_BuR_BUr_buRh4n_h4Un7s_m3_t!L_t0D4y_QsUqWOYSImTdtQ9B}
```

---

## Key Takeaways

**Follow the data flow, not the obfuscated names.** Single-letter class and field names look intimidating, but once you trace which values feed into which hashes, the structure becomes clear. The obfuscation here was cosmetic.

**Overloaded methods can have different semantics.** `p.a(int, byte[])` and `p.a(int, int[])` look like the same function from the outside but use different operation ID tables internally. Checking each overload separately — and verifying inverses by round-tripping random inputs — is the right habit.

**"Hidden in plain sight" is a real design pattern.** The admin password was derived entirely from values the unprivileged user could read. The challenge was noticing this and collecting them in the right order, not cracking anything.

**Compile against the challenge JAR.** When the JAR exposes useful public/static utility methods (here: `p.a` for unranking permutations, hashing, and transformations), calling them directly from a helper class avoids reimplementing complex algorithms and guarantees you match the server's behavior exactly.

**Check attachment hashes.** The JAR was replaced mid-challenge. An otherwise correct solver against the old attachment would always fail Burhan's login. When in doubt, verify `sha256sum burhanquest.jar`.

**Solve scripts:** `Solve.java` (password derivation + flag decryption), `exploit.py` (full automation), `LocalDump.java` (reflection-based debug helper).
