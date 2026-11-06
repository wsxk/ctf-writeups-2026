# Missing One Piece

**Category:** Reverse Engineering<br>
**Points:** 500

## Description

A Linux binary called `missing_one_piece` that prints a sad message when run directly. The binary checks three runtime environment conditions before it will reveal the flag.

## Solution

### Step 1: Initial Reconnaissance

Running the binary as-is gives:
```
$ ./missing_one_piece
It seems the One Piece is nowhere to be found...
```

Running `strings` on the binary reveals the important clues:
```
./devilishFruit
PWD=/tmp/gogear5
ONE_PIECE=IS_REAL
The legends have been proven true! %s
you_dont_need_to_rev_this
```

### Step 2: Reverse the Checks

Decompiling `main()` reveals three conditions:

1. **argv[0] check:** The program expects to be invoked as `./devilishFruit` (it checks `strcmp(*argv, "./devilishFruit")`).
2. **PWD check:** It scans environment variables for `PWD=/tmp/gogear5`, meaning it must be run from inside `/tmp/gogear5`.
3. **Environment variable check:** It looks for a custom env var `ONE_PIECE=IS_REAL`.

When all three pass, the binary concatenates the three strings together, runs them through a transformation function (`you_dont_need_to_rev_this`), and prints the result as the flag.

### Step 3: Satisfy the Conditions

```bash
mkdir -p /tmp/gogear5
cp missing_one_piece /tmp/gogear5/devilishFruit
chmod +x /tmp/gogear5/devilishFruit
cd /tmp/gogear5
ONE_PIECE=IS_REAL ./devilishFruit
```

Output:
```
The legends have been proven true! BCCTF{I_gU3S5_7hAt_Wh1t3BeArD_6uY_W45_TRu7h1n6!}
```

No need to reverse the transformation function -- just satisfy the three runtime conditions and the binary does the work.

## Flag

`BCCTF{I_gU3S5_7hAt_Wh1t3BeArD_6uY_W45_TRu7h1n6!}`
