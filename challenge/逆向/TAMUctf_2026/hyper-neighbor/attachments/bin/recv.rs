use hyper_neighbor::{Channel, create_buffer};
use std::convert::Infallible;
use std::error::Error;

fn main() -> Result<Infallible, Box<dyn Error>> {
    let (array, line_size) = create_buffer("/lib/ld-musl-x86_64.so.1")?;
    let channel = Channel::new(array, line_size);

    loop {
        unsafe {
            let mut buf = [0u8; 128];
            let buf = channel.recv(buf.as_mut_slice());
            println!("{:?}", str::from_utf8(buf)?);
        }
    }
}
