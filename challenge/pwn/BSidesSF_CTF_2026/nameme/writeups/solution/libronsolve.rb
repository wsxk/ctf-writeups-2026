require 'yaml'
require 'tempfile'

METADATA = YAML::load(File.read(File.join(__dir__, '../metadata.yml')))
CHALLENGE_NAME = File.basename(File.expand_path('..', __dir__))
TOOLS_DIR = File.expand_path('../../../tools', __dir__)

if METADATA['service_from_challenge']
  SERVICE_METADATA = YAML::load(File.read(File.join(__dir__, "../../#{ METADATA['service_from_challenge'] }/metadata.yml")))
else
  SERVICE_METADATA = METADATA
end

if !File.directory?(TOOLS_DIR)
  raise "Couldn't find the tools directory, it should be @ #{ TOOLS_DIR }"
end

def expected_flag
  METADATA['flag']
end

def flag_path
  METADATA['flag_path']
end

def protocol
  SERVICE_METADATA['protocol']
end

def generate_hostname
  if METADATA['service_from_challenge']
    `python #{ TOOLS_DIR }/get_hostname.py #{ METADATA['service_from_challenge'] }`.chomp
  else
    `python #{ TOOLS_DIR }/get_hostname.py #{ CHALLENGE_NAME }`.chomp
  end
end

def get_host_port
  if protocol() != 'tcp' && protocol() != 'udp'
    raise "Using get_host_port() on a non-tcp/udp service doesn't make sense!"
  end

  host = ARGV[0] || generate_hostname()
  port = (ARGV[1] || SERVICE_METADATA['port']).to_i

  return host, port
end

def get_url
  if protocol() != 'http'
    raise "Using get_url() on a non-http service doesn't make sense!"
  end

  if ARGV[0]
    if ARGV[0] !~ /^http/
      raise "Usage: #{ $0 } [http[s]://hostname:port/]"
    end

    if ARGV[0][-1] == '/'
      return ARGV[0]
    else
      return "#{ ARGV[0] }/"
    end
  else
    return "https://#{ generate_hostname() }/"
  end
end

def check_flag(flag, terminate: true, partial: true)
  if flag.nil?
    raise "Expected flag, got nil!"
  end

  if flag == ''
    raise "Expected flag, got the empty string!"
  end

  flag = flag.chomp

  if partial
    unless flag =~ /(CTF{[^}]*})/
      raise "Nothing in the data looks like a/the flag: #{ flag } (\"#{ flag.unpack('H*').pop }\")"
    end

    flag = Regexp.last_match(0)
  end

  puts "Fetched flag: #{ flag } (\"#{ flag.unpack('H*').pop }\")"

  if flag != expected_flag()
    raise "We didn't get the correct flag!"
  end

  puts "Looks good!"

  if terminate
    exit 0
  end
end

## Some convenience functions for writing exploits
def get_symbol(lib, symbol, offset = 0)
  # 1009: 0000000000048c10    18 FUNC    WEAK   DEFAULT   16 strtol@@GLIBC_2.2.5
  `readelf -Ws "#{ lib }"`.split(/\n/).each do |line|
    if line =~ /:\s*([0-9a-f]+)\s.*\s#{ symbol }($|@)/
      return Regexp.last_match(1).to_i(16) + offset
    end
  end

  raise "Couldn't find symbol #{ symbol } in #{ lib }!"
end

def quick_disassemble(bytes)
  data = [bytes.gsub(/ /, '')].pack('H*')

  Tempfile.create("test.bin") do |f|
    f.write(data)
    f.close

    begin
      return `ndisasm -b64 "#{ f.to_path }"`&.split(/\r?\n/).map { |d| d.gsub(/.*  /, '') }.join(' / ')
    rescue StandardError => e
      return '(ndisasm required to disassemble)'
    end
  end
end

ROP_CACHE = {}
def get_rop_sequence(lib, op1, op2 = nil, find_possibilities: false)
  # Don't run this over and over
  if ROP_CACHE[lib].nil?
    # 401012:       48 83 c4 08             add    $0x8,%rsp
    segments = []

    # Used to divide the segments
    expected_address = -1

    `objdump -d #{ lib }`.split(/\r?\n/).each do |line|
      # Ignore lines with no tabs
      unless line.include?("\t")
        next
      end

      # Remove special characters
      address, bytes, _etc = line.split(/\t/, 3)

      # This SHOULD always hit
      if bytes
        # puts line
        address = address.to_i(16)
        bytes = [bytes.delete(' ')].pack('H*').unpack('c*')

        # If we've hopped in memory (or are at the start), start a new block
        if address != expected_address
          segments << {
            start: address,
            data: [],
          }
        end

        segments.last[:data].concat(bytes)
        expected_address = address + bytes.length
      end
    end

    segments = segments.map do |segment|
      segment[:data] = segment[:data].map { |b| '%02x' % (b & 0x0FF) }.join(' ') + ' '
      segment
    end

    ROP_CACHE[lib] = segments.clone
  end

  op1 = op1.bytes.map { |b| '%02x' % (b & 0x0FF) }.join(' ')
  op2 = op2&.bytes&.map { |b| '%02x' % (b & 0x0FF) }&.join(' ')

  # ROP_CACHE[lib].each do |r|
  #   puts "%x :: #{ r[:data] }" % r[:start]
  # end

  0.upto(find_possibilities ? 8 : 0) do |i|
    matcher = Regexp.new("#{ op1 } #{ '.. ' * i }#{ op2 || '' }")
    # puts "Searching for: #{ matcher }..."

    ROP_CACHE[lib].each do |segment|
      index = segment[:data] =~ matcher
      unless index.nil?
        index = index / 3 # Because each byte is represented by 3 characters
        if i == 0
          if find_possibilities
            puts 'FOUND GOOD: %x' % [segment[:start] + index]
          else
            return segment[:start] + index
          end
        else
          bytes = Regexp.last_match(0)
          asm = quick_disassemble(bytes)
          puts "FOUND POSSIBILITY: %d bytes away: %x :: #{ bytes } :: #{ asm }" % [i, segment[:start] + index]
        end
      end
    end
  end

  if find_possibilities
    puts 'Possibilitie(s) are above!'
    exit
  else
    raise "Couldn't find ROP sequence! Set find_possibilities: true to search!"
  end
end


puts "Loading checker..."
puts '--------'
puts "Challenge name:        #{ CHALLENGE_NAME }"
puts "Expected flag:         #{ expected_flag() } (\"#{ expected_flag().unpack('H*').pop }\")"
case protocol()
when 'http'
  puts "Using URL:             #{ get_url() }"
when 'tcp'
  puts "Using TCP host/port:   #{ get_host_port().join(':') }"
when 'udp'
  puts "Using UDP host/port:   #{ get_host_port().join(':') }"
else
  puts "Offline challenge"
end
puts '--------'
