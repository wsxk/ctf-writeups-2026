# Abyss Oracle

## Handout issue

The shipped `bzImage` is Kali 6.19.14, but `abyss_oracle.ko` was built for
`6.12.95+deb13-cloud-amd64` with modversions.  Consequently, the untouched
`run-qemu.sh` cannot load the module.  `patch-local.py` makes only the local
ABI-compatibility changes needed to test it with the supplied bzImage:
vermagic, the moved `struct module::exit`, the 6.19 stack-canary ABI, and a
small in-module mutex initializer because `__mutex_init` is no longer exported.
The original module remains at `extracted/abyss_oracle-original.ko`.

There is also a cosmetic shell bug in `run-qemu.sh`: the default containing a
`}` in `LOCAL_FLAG="${LOCAL_FLAG:-CTF{local_test_only}}"` leaves an extra final
brace whenever `LOCAL_FLAG` is explicitly set.

## Vulnerability / capability chain

The following ioctl chain turns the intended capability API into arbitrary
kernel read/write:

1. Create two capabilities with flags `0x1f` and seal both.
2. Alias capability A.  Retire the original A handle, changing the still-live
   aliased object to state 4.
3. Merge state-4 A with sealed B.  The merged object inherits read/write flags
   and receives privileged flag `0x20`.
4. `AB_LEAK` on the merged object discloses its nonce, encoded/decoded base,
   and `init_task`.  Thus the context secret is:

       secret = encoded ^ decoded ^ rol64(nonce, 17)

5. `AB_BIND` accepts a new encoded kernel base and a length up to 0x400.
   Re-encode any desired target using the recovered secret.
6. `AB_READ` is now an arbitrary kernel read. `AB_WRITE` is an arbitrary
   direct-map write; its supplied qword must first be XORed with
   `0xa55a5aa55aa55aa5`.

`exploit.c` uses the primitive to locate the task-list, PID, and credential
fields dynamically (rather than hardcoding 6.19 offsets), finds its own
`task_struct`, and replaces `real_cred` and `cred` with `init_cred`.

## Local build/run

```sh
gcc -static -O2 -Wall -Wextra -s -o exploit exploit.c
python3 patch-local.py
(cd extracted && find . -print0 | cpio --null -o --format=newc --quiet \
  | gzip -9 > ../local-initramfs.cpio.gz)
LOCAL_FLAG='CTF{local_test}' INITRAMFS="$PWD/local-initramfs.cpio.gz" \
  bash ./run-qemu.sh ./exploit
```

Successful local output includes:

```
[+] credentials replaced, uid=0 euid=0
[+] FLAG: CTF{local_test}}
```

(The second closing brace is the `run-qemu.sh` issue described above.)
