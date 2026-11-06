use hyper_neighbor::{Channel, create_buffer};
use std::convert::Infallible;
use std::error::Error;
use std::time::Duration;
use std::{env, fs, thread};

fn main() -> Result<Infallible, Box<dyn Error>> {
    let file = fs::read(env::args().nth(1).expect("Need a file to send!"))?;

    let (array, line_size) = create_buffer(
        env::args()
            .nth(2)
            .expect("Need a file to send to!")
            .as_str(),
    )?;
    let channel = Channel::new(array, line_size);

    loop {
        unsafe {
            channel.send(&file);
        }
        thread::sleep(Duration::from_secs(1));
    }
}
