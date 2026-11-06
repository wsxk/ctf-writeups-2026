# garden

This is a pwn challenge that uses a memory cage for its heap.

```c
typedef enum {
    PUSH_NUM_ARRAY, ADD_NUMS, SUB_NUMS, MUL_NUMS, DIV_NUMS, MOD_NUMS,
    GET_ELEM_OBJ, SET_ELEM_OBJ, GET_ELEM_NUM, SET_ELEM_NUM, PRINT_NUM_ARRAY,
    GET_OFFHEAP_NUM, SET_OFFHEAP_NUM,
    NEW_ARRAY_OBJ, NEW_ARRAY_NUM, NEW_OFFHEAP_OBJ,
    DUP, SWAP, DROP, DUP_X1,
    GARBAGE_COLLECT
} opcode_t;
```

There are three types of objects in this system: numerical arrays, object arrays, and off-heap numerical arrays.
Objects are reference-traced and garbage collected using a mark-sweep heap compaction algorithm.
The user is allowed to submit a list of instruction opcodes at the start, and then the VM interprets the bytecodes.
Since there is no user input in the VM, all the exploit logic needs to be embedded in the VM program itself.

## Important Bugs
The null pointer (which can be obtained from reading a reference from an unintialized array)
isn't explicitly checked in the VM; it is a valid heap address which should read zero bytes.
The VM type confuses it as a zero-length num array.

If the mark_reachable gc function is changed so that it only checks if the pointer is null
for recursive calls and not at the beginning of the function, then a nullpointer on the stack will
be added as a root and included in the heap compaction.

This will lead to a placement error when compacting the heap; when finding a new location for the
4-byte null object, it might actually cause other objects in the heap to relocate upwards, corrupting
the start of other objects in the heap. This would allow numerical data to be able to overwrite the start
of next objects in the heap, rewriting their `length` and `mark_word` values.

This would give us the capability to rewrite arbitrary numerical arrays as if they were off-heap objects.
Imagine this heap construct, where we allocate two numerical arrays with values 
`[a]` and `[w x y z]`:
The heap would read:
```
[uint16_t][uint16_t][     uint32_t     ][uint16_t][uint16_t] (more data...)
[ length ][mrk_word][        a         ][ length ][mrk_word] (w, x, y, z)
```

The addition of the null object would force object reloaction to shift to the right by four bytes.
All the pointers get updated correctly, but the memmove, only being run on each object one at a time,
would corrupt the beginning sections of next object in the heap.
This would cause the `uint32_t` number `a` to overwrite the `uint16_t length` and `uint16_t mark_word` fields
of the second object. If the payload value `a` is designed correctly, then the new object could become
an off-heap object. In this case, the values of `uint32_t w, x, y, z` would be interpreted as the struct
fields of an `off_heap_obj_t`, i.e. `uint32_t *data; size_t obj_size;`.
This creates an arbitrary read-write primitive.

We can also do the reverse transformation, converting an off-heap pointer back into raw data to be analyzed.
This is used in the exploit process.

Edit: there was also a bug with the `alloc_off_heap` total_size calculation, which led to an unintended solution
using integer overflow to corrupt the heap. Oops!

## Exploit
We can leak a memmapped address by requesting a large off-heap object:
```py
push_literal_arr(asm, [0x100000])
asm.append(NEW_OFFHEAP_OBJ)
```
On this operating system, the libc base can be deterministally calculated
using an offset:
```
0x7009dfdff010 - 0x10 + (0x7ffff7c00000 - 0x7ffef77ff000)
= 0x700ae0200000
0x700ae0200000  /usr/lib/x86_64-linux-gnu/libc.so.6
```
The `environ` libc variable is stored at `0x20ad58` after the libc start:
```
0x700ae040ad58 - 0x700ae0200000
= 0x20ad58
```
Behind the `environ` pointer, we leak a stack address.
```
pwndbg> x/gx 0x700ae040ad58.
0x700ae040ad58 <environ>:       0x00007ffe1a787a28
```
Using GDB, we can find the saved rip location on the stack:
```
pwndbg> info frame 1
Stack frame at 0x7ffe1a7878d0:
 rip = 0x5bfbf04f43a9 in interpret; saved rip = 0x5bfbf04f44f4
 called by frame at 0x7ffe1a787900, caller of frame at 0x7ffe1a787700
 Arglist at 0x7ffe1a7878c0, args: 
 Locals at 0x7ffe1a7878c0, Previous frame's sp is 0x7ffe1a7878d0
 Saved registers:
  rbx at 0x7ffe1a7878b8, rbp at 0x7ffe1a7878c0, rip at 0x7ffe1a7878c8
```
This means that we can construct a rop chain using an offset of
`0x7ffe1a7878c8 - 0x00007ffe1a787a28 = -0x160` from the `environ` pointer.

## Solution
This was my steps to solving the challenge:
1. Allocate a large off-heap object, forcing `malloc` to `mmap` a new region.
2. Use the gc bug to corrupt the object header, converting it into numerical data.
3. Use pointer arithmetic to calculate the leaked location of libc.
4. Use the gc bug to convert our calculated pointer into an off-heap object to read the libc `environ` variable.
5. Load the pointer stored in the `environ` variable. This leaks a pointer to the stack.
6. Using the leaked libc base, calculate pointers to rop gadgets to initialize a ret2libc rop chain on the stack.
7. Exit, allowing the rop chain attack to `system /bin/sh` shell access.

At the bottom, this challenge is just about getting RCE from some arbitrary read/write primitives.
What makes this challenge difficult is the fact that there is no i/o, meaning that all the pointer leaking logic
has to be done within the VM. Additionally, the heap is caged; the only external pointers you can derive are for
malloc-ed off-heap memory, which is never freed. The only way to exploit the custom heap is by exploiting a
niche bug in the garbage collection code; a small error in its mark phase causes it to try to relocate
null objects onto the stack, which can cause corruption during compacting because it breaks the monotonic guarantees
of the heap compaction algorithm. If we try to include the null object, relocation might actually move objects upwards
instead of downwards, which can cause four bytes of neighboring objects to get overwritten during the `memmove`.
Only by carefully exploiting this primitive can we escape the memory cage and pwn the system.
