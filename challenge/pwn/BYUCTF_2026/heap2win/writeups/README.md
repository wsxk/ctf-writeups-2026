# Heap 2 Win

Remember me? No one solved me during kickstart, so I'm back for revenge

Files:
- [heap2win.zip](./heap2win.zip)

### Solve

This is a fun challenge because it's *very* specific to C++ as far as the vulnerability goes. It involves an overwrite in the heap (line 32: `scanf("%s", name);`) combined with the fact that the whole binary is using classes with virtual functions.

In C++, a virtual function uses what is called a vtable, which contains pointers to all of the relevant functions. This way, the heap stores a base object that looks something like vtable pointer followed by all the other members, then to actually call functions it dereferences the vtable. So all you need to do is change what the vtable is pointing to and voila, you have function call capability.

This one is pretty easy because I give a `WinnerButton`, which has all of the same functions as a normal buttons but `push` calls `/bin/sh` for them. They just need to use their overwrite to overwrite an old button's vtable pointer with that of a `WinnerButton` and then push it. 

[solve.py](./solve.py) has a working, automatic solve. Turns out, when you use vectors, it'll store temporary data on the heap at just the right size for our object to inject itself at an old index, which I discovered through debugging. Works like a charm

Flag: `byuctf{y34h,..._you're_a_pro}`