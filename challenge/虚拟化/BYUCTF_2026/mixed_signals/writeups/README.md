# Mixed Signals

### Description

Legend has it, this checks a flag

Files:
- [mixed_signals](./mixed_signals)
- [program](./program)

### Solve

`mixed_signals` is a VM that is based on signals sent to the program. `program` has a number of signals that it throws at `mixed_signals` that triggers actions in the VM that checks the inputted flag *in constant time* (that's important lol). Basically we put the flag in a data section in `mixed_signals`, then the opcodes sent by `program` actually go through and do stuff to it. If you reverse it, you can verify that you have the right flag by running `./mixed_signals <flag>` then running `./program` in a separate tab (they interact).

There is no solve script for this one

Flag: `byuctf{l3ft_bl1nk3r_5c9125be}`