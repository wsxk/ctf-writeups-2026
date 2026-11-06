SHELL := /bin/bash

DOCKER ?= docker
OUTDIR ?= build
OUTDIR_SOLVE ?= build-solve
JAIL_IMAGE ?= challenge-jail
JAIL_PORT ?= 5000
HOST ?= localhost
PORT ?= 5000
MUSL_CC ?= musl-gcc
SOLVER_SRC ?= rootfs/user.c
SOLVER_BIN ?= $(OUTDIR)/solver
SOLVER_XZ ?= $(SOLVER_BIN).xz
SOLVER_CFLAGS ?= -O2 -static -s
QEMU ?= qemu-system-x86_64
KERNEL_CMDLINE ?= console=ttyS0 loglevel=3 panic=-1 oops=panic init=/init
QEMU_FLAGS ?= -m 2G -smp 2 -nographic -no-reboot -monitor /dev/null

.PHONY: help build build-solve run run-solve run-jail solve-jail clean check-run-tools solver solver-xz

help:
	@echo "Targets:"
	@echo "  make build      Build Docker artifacts to $(OUTDIR)"
	@echo "  make run        Build and boot challenge image (no solver)"
	@echo "  make run-solve  Build and boot challenge image with /user solver"
	@echo "  make run-jail   Build pwn.red/jail image and expose it on $(JAIL_PORT)"
	@echo "  make solver-xz  Build stripped static solver and compress with xz"
	@echo "  make solve-jail Upload solver to HOST:PORT and execute it"
	@echo "  make clean      Remove build output directories"

build:
	@command -v $(DOCKER) >/dev/null || { echo "error: $(DOCKER) is required"; exit 1; }
	@mkdir -p "$(OUTDIR)"
	$(DOCKER) build . --target artifacts -o "$(OUTDIR)"

build-solve:
	@command -v $(DOCKER) >/dev/null || { echo "error: $(DOCKER) is required"; exit 1; }
	@mkdir -p "$(OUTDIR_SOLVE)"
	$(DOCKER) build . --target artifacts --build-arg INCLUDE_SOLVER=1 -o "$(OUTDIR_SOLVE)"

check-run-tools:
	@command -v $(QEMU) >/dev/null || { echo "error: $(QEMU) is required"; exit 1; }

run: build check-run-tools
	"$(QEMU)" \
		-kernel "$(OUTDIR)/bzImage" \
		-initrd "$(OUTDIR)/initramfs.cpio.gz" \
		-append "$(KERNEL_CMDLINE)" \
		$(QEMU_FLAGS)

run-solve: build-solve check-run-tools
	"$(QEMU)" \
		-kernel "$(OUTDIR_SOLVE)/bzImage" \
		-initrd "$(OUTDIR_SOLVE)/initramfs.cpio.gz" \
		-append "$(KERNEL_CMDLINE)" \
		$(QEMU_FLAGS)

run-jail:
	@command -v $(DOCKER) >/dev/null || { echo "error: $(DOCKER) is required"; exit 1; }
	$(DOCKER) build . --target jail -t "$(JAIL_IMAGE)"
	$(DOCKER) run --rm -it --privileged -p "$(JAIL_PORT):$(JAIL_PORT)" "$(JAIL_IMAGE)"

$(SOLVER_BIN): $(SOLVER_SRC)
	@mkdir -p "$(OUTDIR)"
	@command -v $(MUSL_CC) >/dev/null || { echo "error: $(MUSL_CC) is required"; exit 1; }
	$(MUSL_CC) $(SOLVER_CFLAGS) -o "$(SOLVER_BIN)" "$(SOLVER_SRC)"

solver: $(SOLVER_BIN)

$(SOLVER_XZ): $(SOLVER_BIN)
	@command -v xz >/dev/null || { echo "error: xz is required"; exit 1; }
	xz -z -c -9e "$(SOLVER_BIN)" > "$(SOLVER_XZ)"

solver-xz: $(SOLVER_XZ)

solve-jail: solver-xz
	@command -v python3 >/dev/null || { echo "error: python3 is required"; exit 1; }
	python3 ./scripts/upload_solver.py "$(HOST)" "$(PORT)" "$(SOLVER_XZ)"

clean:
	rm -rf "$(OUTDIR)" "$(OUTDIR_SOLVE)"
