# explorer
## rust kernel reversing

/dev/challenge exposes a maze game. connecting to it and using the correct ioctl will give us the seed and maze dimensions
follow the kernel algorithm to recreate the maze in userspace
BFS to find the solution to the maze
navigating to the end will allow retrieving the flag
solver in rootfs/user.c
maze visualiser in `scripts/maze_viz.py`

## building

```
  make build      Build Docker artifacts to build
  make run        Build and boot challenge image locally (no solver)
  make run-solve  Build and boot challenge image locally with solver
  make run-jail   Build pwn.red/jail image and expose it on 5000
  make solver-xz  Build stripped static solver and compress with xz
  make solve-jail Upload solver to HOST:PORT and execute it
  make clean      Remove build output directories
```

## dist

modify the flag in `challenge.rs` and run `make build`, then copy the files in `build` to `dist`
