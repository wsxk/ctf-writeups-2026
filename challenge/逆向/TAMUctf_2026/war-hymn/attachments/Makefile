
NAME := war-hymn

DOCKER_CONTEXT := default
DOCKER_GLOBAL := --context $(DOCKER_CONTEXT)

# Compile the main program 
# Compile decrypt function, extract its .text section, and embed it into the main program
# Compile shared library, zlib compress and encrypt it, and embed it into the main program
compile:

	gcc war-hymn.c -o $(NAME) -lz -ldl -fno-pie -no-pie -O2

	gcc -c decrypt.c \
		-O2 \
		-fno-pie \
		-fno-inline \
		-fno-stack-protector \
		-mno-red-zone \
		-ffreestanding \
		-nostdlib \
		-o decrypt.o

	objcopy -O binary --only-section=.text decrypt.o decrypt.bin

	objcopy \
		--add-section .init.checksum.validation=decrypt.bin \
		--set-section-flags .init.checksum.validation=alloc,load,data \
		$(NAME)


	gcc -shared -fPIC -fvisibility=hidden \
    -o shared.so shared.c

	python3 perform_zlib_compression.py

	python3 make_encrypted_zlib.py

	objcopy \
		--add-section .bss.secure.buffer=encrypted_zlib.bin \
		--set-section-flags .bss.secure.buffer=alloc,readonly \
		$(NAME)

	strip $(NAME)

build: Dockerfile
	docker $(DOCKER_GLOBAL) build -t $(NAME) .

extract: build
	$(eval id := $(shell docker create $(NAME)))
	docker cp $(id):/tmp/$(NAME) .
	docker rm -v $(id)

dist: extract
	tar -czvf $(NAME).tar.gz $(NAME)

clean:

	rm -f $(NAME) $(NAME).tar.gz decrypt.o decrypt.bin shared.so shared.so.deflate shared.so.zlib encrypted_zlib.bin

.PHONY: compile build extract dist clean