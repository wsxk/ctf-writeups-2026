#!/usr/bin/env bash
set -euo pipefail

PACK_NAME="${1:?Usage: ./compile.sh <pack_name>}"

RUNTIME_CFLAGS=(
  -O3
  -msha
  -std=gnu11
  -fno-stack-protector
  -fno-unwind-tables
  -fno-asynchronous-unwind-tables
  -fno-ident
  -Wno-return-stack-address
  -no-pie
  -Wl,--build-id=none
  -Wl,--no-eh-frame-hdr
)

PACKED_DROP_SECTIONS=(
  .eh_frame
  .eh_frame_hdr
  .comment
  .note.gnu.property
  .note.ABI-tag
  .note.gnu.build-id
  .gnu.build.attributes
  .annobin.notes
)

clang "${RUNTIME_CFLAGS[@]}" "generated_code_${PACK_NAME}.c" -o "unpacked_${PACK_NAME}" && \
objdump -d "unpacked_${PACK_NAME}" -M intel > "dump_${PACK_NAME}.asm" && \
clang -O3 -msha -no-pie "generated_encrypt_${PACK_NAME}.c" -o "generated_encrypt_${PACK_NAME}" && \
"./generated_encrypt_${PACK_NAME}" "unpacked_${PACK_NAME}" "secret_input_${PACK_NAME}" "packed_${PACK_NAME}" > "encryption_log_${PACK_NAME}.txt" && \
chmod +x "packed_${PACK_NAME}" && \
strip --strip-all "packed_${PACK_NAME}"

for section in "${PACKED_DROP_SECTIONS[@]}"; do
  objcopy --remove-section="${section}" "packed_${PACK_NAME}"
done
