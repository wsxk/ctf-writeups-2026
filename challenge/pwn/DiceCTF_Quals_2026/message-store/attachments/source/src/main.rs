use std::{
    cell::UnsafeCell,
    io::{BufRead, Write},
    str::FromStr,
};

use colored::Colorize;

#[derive(Debug)]
struct SyncUnsafeCell<T: ?Sized> {
    value: UnsafeCell<T>,
}

unsafe impl<T: ?Sized + Sync> Sync for SyncUnsafeCell<T> {}

// Ensure this is aligned so that we can access it OOB from the jump table
#[repr(C, align(8))]
pub struct Buffer<const N: usize>(SyncUnsafeCell<[u8; N]>);

impl<const N: usize> Buffer<N> {
    fn get(&self) -> &[u8] {
        unsafe { &*self.0.value.get() }
    }

    fn get_mut(&self) -> &mut [u8] {
        unsafe { &mut *self.0.value.get() }
    }

    fn write(&self, data: &[u8]) {
        let slice: &mut [u8] = self.get_mut().get_mut(..data.len()).unwrap();
        slice.copy_from_slice(data);
    }
}

const BUF_SIZE: usize = 0x1000;

static BUFFER: Buffer<BUF_SIZE> = const { unsafe { Buffer(std::mem::transmute([0u8; BUF_SIZE])) } };

static COLOR: SyncUnsafeCell<MessageColor> = SyncUnsafeCell {
    value: UnsafeCell::new(MessageColor::White),
};

fn set_color(color: MessageColor) {
    unsafe { *COLOR.value.get() = color }
}

fn get_color() -> MessageColor {
    unsafe { *COLOR.value.get() }
}

#[inline(never)]
fn input(prompt: &str) -> std::io::Result<String> {
    let mut buf = String::new();
    print!("{prompt}");
    std::io::stdout().flush().unwrap();
    std::io::stdin().read_line(&mut buf)?;
    buf = buf.trim().to_string();
    Ok(buf)
}

#[inline(never)]
fn input_bytes(prompt: &str) -> std::io::Result<Vec<u8>> {
    let mut buf = Vec::new();
    print!("{prompt}");
    std::io::stdout().flush().unwrap();
    std::io::stdin().lock().read_until(b'\n', &mut buf)?;
    buf.pop_if(|c| *c == b'\n');
    Ok(buf)
}

#[inline(never)]
fn input_parsed<T: FromStr>(prompt: &str) -> std::io::Result<Option<T>> {
    Ok(input(prompt)?.parse().ok())
}

#[inline(never)]
fn set_message() -> std::io::Result<()> {
    let message = input_bytes("New Message? ")?;
    if message.len() > BUF_SIZE {
        eprintln!("message too long");
        return Ok(());
    }
    BUFFER.write(&message);
    Ok(())
}

#[derive(Copy, Clone, Debug)]
#[repr(usize)]
#[allow(dead_code)]
enum MessageColor {
    Red = 0,
    Green = 1,
    Yellow = 2,
    Blue = 3,
    Magenta = 4,
    Cyan = 5,
    White = 6,
}

#[inline(never)]
fn set_message_color() -> std::io::Result<()> {
    let Some(color) = input_parsed::<usize>(
        "-- Message Colors -- \n\
            0) Red \n\
            1) Green \n\
            2) Yellow \n\
            3) Blue \n\
            4) Magenta \n\
            5) Cyan \n\
            6) White \n\
            > \
            ",
    )?
    else {
        return Ok(());
    };
    set_color(unsafe { std::mem::transmute(color) });
    Ok(())
}

#[inline(never)]
fn print_message() -> std::io::Result<()> {
    let message = String::from_utf8_lossy(BUFFER.get());
    // If `COLOR` is an invalid enum value, this goes OOB of the jump table
    let func = match get_color() {
        MessageColor::Red => Colorize::red,
        MessageColor::Green => Colorize::green,
        MessageColor::Yellow => Colorize::yellow,
        MessageColor::Blue => Colorize::blue,
        MessageColor::Magenta => Colorize::magenta,
        MessageColor::Cyan => Colorize::cyan,
        MessageColor::White => Colorize::white,
    };
    println!("{}", func(&*message));

    Ok(())
}

// 🤪
// Strip this symbol from release
#[unsafe(naked)]
#[unsafe(no_mangle)]
pub extern "C" fn gadget() -> ! {
    core::arch::naked_asm!("xchg rax, rsp; ret;");
}

fn main() -> std::io::Result<()> {
    loop {
        let Some(menu_opt) = input_parsed::<u8>(
            "-- MESSAGE STORER -- \n\
            1) Set Message \n\
            2) Set Message Color \n\
            3) Print Message \n\
            4) Exit \n\
            > \
            ",
        )?
        else {
            eprintln!("couldn't parse");
            continue;
        };
        match menu_opt {
            1 => set_message()?,
            2 => set_message_color()?,
            3 => print_message()?,
            4 => {
                return Ok(());
            }
            _ => eprintln!("unrecognized menu option {menu_opt}"),
        }
    }
}
