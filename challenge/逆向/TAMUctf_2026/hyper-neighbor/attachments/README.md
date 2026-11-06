# hyper-neighbor

Author: `addison`

Somewhere, somehow, a neighbor is running the attached binary with the following command:

```bash
hyper-neighbor flag.txt /lib/libc.musl-x86_64.so.1
```

I have no idea what it's doing, or how we can try to read the flag.
Give it a go?

## Challenge files

Please presume you are only given the output of `make dist`.
Reading anything else is off-limits, as it will instantly reveal the challenge context.
Any existing debug materials made available here might not even be relevant for your computer, so don't even try. :)

## Local testing

```
nc localhost 6969
```

## Infrastructure notes

This challenge only will build and work on x86 processors.
For jail support, you may need to set the following on recent Ubuntu:
```
sudo sysctl -w kernel.apparmor_restrict_unprivileged_unconfined=0
sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0
```

<details>

<summary>
Click to reveal an infrastructure note that is potentially spoiler-y.
</summary>

This only works when the cores assigned in the Makefile are hyperthread neighbors, or at least share an l3 cache.
Additionally, this means that this challenge _does not scale_.
It might also mean that it doesn't even work in a VM.

</details>

## Solution

This is a Flush+Reload side channel attack, except being used to share data. The binary is designed to be run on two hyperthread neighbors, and it uses the shared L3 cache to communicate. The first process will read the flag and then do some complicated cache manipulation to encode the flag into the cache, while we have to implement the recieving side of the attack to read the flag out of the cache.

The message is transmitted 32 bits at a time with a CRC32 checksum across 64 lines of cache. Each bit that is equal to 1 in the message will flush its corresponding cache line, while bits that are 0 will leave the cache line alone. From the reciever side, this means lines that take longer to access correspond to bits that are 1, while lines that are faster to access correspond to bits that are 0. By measuring the access times of the cache lines and using the checksum, we can reconstruct the original message.

See `solve.c` for an implementation of the reciever.

flag:
`gigem{you-really-need-to-calm-down-10aa082660957ffe}`
