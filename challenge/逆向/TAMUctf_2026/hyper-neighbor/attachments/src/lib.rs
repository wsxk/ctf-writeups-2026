#![allow(unsafe_op_in_unsafe_fn)]

extern crate alloc;
extern crate core;

use alloc::boxed::Box;
use cache_size::l3_cache_line_size;
#[cfg(feature = "recv")]
use core::arch::x86_64::__rdtscp;
#[cfg(feature = "recv")]
use core::arch::x86_64::_MM_HINT_T0;
use core::arch::x86_64::_mm_clflush;
#[cfg(feature = "recv")]
use core::arch::x86_64::_mm_prefetch;
use core::error::Error;
use core::num::NonZeroUsize;
use core::ptr::NonNull;
#[cfg(feature = "recv")]
use core::ptr::read_volatile;
use core::{mem, slice};
use nix::sys::mman::{MapFlags, ProtFlags, mmap};
use std::arch::x86_64::{_mm_crc32_u16, _mm_crc32_u32};
use std::fs::File;
use std::os::fd::AsFd;

const TRANSMIT_FLUSH_COUNT: u64 = 500_000;
#[cfg(feature = "recv")]
const MEASUREMENT_POSITIVE_THRESHOLD: u64 = 25;

const BASE: usize = 0xdeadbeefdeadbeef;
const START: u64 = 0xdeadbeef00000001;
const END: u64 = 0xdeadbeef00000002;
const SIZE: usize = 0x1000;

#[cfg(feature = "recv")]
const PREFETCHES: u64 = 32;
#[cfg(feature = "recv")]
const MEASUREMENTS: u64 = 32;

pub fn create_buffer(path: &str) -> Result<(&'static [u8], usize), Box<dyn Error>> {
    let line_size = l3_cache_line_size().unwrap();
    let base_address = BASE & !(line_size - 1); // alignment

    let file = File::open(path)?;

    let address: NonNull<u8> = unsafe {
        mmap(
            NonZeroUsize::new(base_address),
            NonZeroUsize::new_unchecked(SIZE * line_size),
            ProtFlags::PROT_READ,
            MapFlags::MAP_SHARED,
            file.as_fd(),
            0,
        )?
    }
    .cast();
    let array = unsafe { slice::from_raw_parts(address.as_ptr(), SIZE) };
    Ok((array, line_size))
}

pub struct Channel<'a> {
    base: &'a [u8],
    line_size: usize,
}

#[repr(C, packed)]
#[derive(Copy, Clone)]
struct Message {
    value: [u8; size_of::<u32>()],
    idx: u16,
    chk: u16,
}

// the rest of this file is largely based on:
// https://github.com/Peribunt/CTC

impl Message {
    fn chksum(value: [u8; size_of::<u32>()], idx: u16) -> u16 {
        const SEED: u32 = 0xdeadbeef;

        let mut chk = SEED;
        unsafe {
            chk = _mm_crc32_u32(chk, u32::from_ne_bytes(value));
            chk = _mm_crc32_u16(chk, idx);
        }
        chk as u16 ^ (chk >> 16) as u16
    }

    fn new(value: [u8; size_of::<u32>()], idx: u16) -> Self {
        Self {
            value,
            idx,
            chk: Self::chksum(value, idx),
        }
    }

    #[cfg(feature = "recv")]
    fn check(self) -> bool {
        self.chk == Self::chksum(self.value, self.idx)
    }
}

impl<'a> Channel<'a> {
    pub fn new(base: &'a [u8], line_size: usize) -> Self {
        Self { base, line_size }
    }

    unsafe fn as_offset<T>(&self, line: usize) -> *const T {
        self.base
            .as_ptr()
            .byte_offset((line * self.line_size) as isize) as *const T
    }

    #[cfg(feature = "recv")]
    unsafe fn measure_line_internal(&self, line: usize) -> u64 {
        let mut junk = 0;
        let addr = self.as_offset(line);

        let init = __rdtscp(&mut junk);
        junk = read_volatile(addr);
        __rdtscp(&mut junk) - init
    }

    #[cfg(feature = "recv")]
    unsafe fn measure_line(&self, line: usize) -> u64 {
        let mut sum = 0;

        _mm_prefetch::<_MM_HINT_T0>(self.as_offset(line));

        for _ in 0..PREFETCHES {
            sum += self.measure_line_internal(line);
        }

        sum / PREFETCHES
    }

    #[cfg(feature = "recv")]
    unsafe fn is_line_positive(&self, line: usize) -> bool {
        let mut likelihood = 0;

        for _ in 0..MEASUREMENTS {
            if self.measure_line(line) > MEASUREMENT_POSITIVE_THRESHOLD {
                likelihood += 1;
            }
        }

        likelihood > (MEASUREMENTS >> 1)
    }

    #[inline(always)]
    unsafe fn set_lines(&self, value: u64) {
        for _ in 0..TRANSMIT_FLUSH_COUNT {
            for i in 0..(size_of::<u64>() * 8) {
                if value & (1 << i) != 0 {
                    _mm_clflush(self.as_offset(i));
                }
            }
        }
    }

    #[cfg(feature = "recv")]
    #[inline(always)]
    unsafe fn load_lines(&self) -> u64 {
        let mut samples = [(0u64, 0usize); MEASUREMENTS as usize];

        for _ in 0..samples.len() {
            let mut current = 0;
            for i in 0..(size_of::<u64>() * 8) {
                current = current | ((self.is_line_positive(i) as u64) << i);
            }

            for sample in &mut samples {
                if sample.0 == current {
                    sample.1 += 1;
                    break;
                } else if sample.0 == 0 && sample.1 == 0 {
                    sample.0 = current;
                    sample.1 = 1;
                }
            }
        }

        samples.into_iter().max_by_key(|v| v.1).unwrap().0
    }

    pub unsafe fn send(&self, data: &[u8]) {
        assert!(data.len() < u16::MAX as usize);

        self.set_lines(START);
        for (i, v) in data.chunks(size_of::<u32>()).enumerate() {
            let mut value = [0u8; size_of::<u32>()];
            value[..v.len()].copy_from_slice(v);
            let block = Message::new(value, i as u16);
            let block: u64 = mem::transmute(block);

            self.set_lines(block);
        }
        self.set_lines(END);
    }

    #[cfg(feature = "recv")]
    pub unsafe fn recv<'b>(&self, data: &'b mut [u8]) -> &'b [u8] {
        while self.load_lines() != START {}

        let mut recvd = 0;
        loop {
            let value = self.load_lines();
            if value == END {
                break &data[..recvd];
            }

            let block: Message = mem::transmute(value);
            if block.check() {
                for (i, v) in block.value.into_iter().enumerate() {
                    if let Some(e) = data.get_mut(i + (block.idx as usize) * 4) {
                        *e = v;
                    }
                }
                recvd = recvd.max((block.idx as usize + 1) * 4);
            }
        }
    }
}
