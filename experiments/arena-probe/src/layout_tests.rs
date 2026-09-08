//! Direct tests execute in the C-started no_std image, never the std test harness.
use crate::{
    arena::{ALLOCATOR, CAPACITY},
    require,
};
use core::{
    alloc::{GlobalAlloc, Layout},
    ptr,
};

fn layout(size: usize, alignment: usize) -> Layout {
    Layout::from_size_align(size, alignment).unwrap()
}

/// Discover once, then require the identical large block after each lifecycle.
pub fn large_probe(size: usize) {
    let before = ALLOCATOR.snapshot();
    let layout = layout(size, 16);
    // SAFETY: nonzero valid layout; checked successful pointer; matching free.
    unsafe {
        let block = ALLOCATOR.alloc(layout);
        require(!block.is_null());
        ptr::write_bytes(block, 0x6d, size);
        require(*block == 0x6d && *block.add(size - 1) == 0x6d);
        ALLOCATOR.dealloc(block, layout);
    }
    let after = ALLOCATOR.snapshot();
    require(after.same_live(&before));
    require(after.allocations == before.allocations + 1);
    require(after.deallocations == before.deallocations + 1);
    ALLOCATOR.check_canaries();
}

pub fn run() {
    ALLOCATOR.require_empty();
    // SAFETY throughout: every layout is valid and nonzero. Only successful,
    // live pointers are read/written, and every free uses the current layout.
    unsafe {
        let mut pointers = [ptr::null_mut(); 13];
        for (power, pointer) in pointers.iter_mut().enumerate() {
            let size = 17 + power * 7;
            *pointer = ALLOCATOR.alloc(layout(size, 1 << power));
            require(!pointer.is_null());
            require((*pointer as usize).is_multiple_of(1 << power));
            ptr::write_bytes(*pointer, power as u8, size);
        }
        for (power, pointer) in pointers.iter().enumerate().rev() {
            let size = 17 + power * 7;
            require(
                core::slice::from_raw_parts(*pointer, size)
                    .iter()
                    .all(|b| *b == power as u8),
            );
            ALLOCATOR.dealloc(*pointer, layout(size, 1 << power));
        }
        let zero_layout = layout(333, 256);
        let dirty = ALLOCATOR.alloc(zero_layout);
        require(!dirty.is_null());
        ptr::write_bytes(dirty, 0xff, 333);
        ALLOCATOR.dealloc(dirty, zero_layout);
        let zero = ALLOCATOR.alloc_zeroed(zero_layout);
        require(!zero.is_null());
        require(
            core::slice::from_raw_parts(zero, 333)
                .iter()
                .all(|b| *b == 0),
        );
        ALLOCATOR.dealloc(zero, zero_layout);

        let old_layout = layout(73, 64);
        let old = ALLOCATOR.alloc(old_layout);
        require(!old.is_null());
        for i in 0..73 {
            old.add(i).write(i as u8);
        }
        let grown = ALLOCATOR.realloc(old, old_layout, 4099);
        require(!grown.is_null() && (grown as usize).is_multiple_of(64));
        for i in 0..73 {
            require(grown.add(i).read() == i as u8);
        }
        // Default realloc keeps both live until the copy finishes.
        require(ALLOCATOR.snapshot().peak_requested == 73 + 4099);
        let shrunk = ALLOCATOR.realloc(grown, layout(4099, 64), 31);
        require(!shrunk.is_null() && (shrunk as usize).is_multiple_of(64));
        for i in 0..31 {
            require(shrunk.add(i).read() == i as u8);
        }
        let before = ALLOCATOR.snapshot();
        let failed = ALLOCATOR.realloc(shrunk, layout(31, 64), CAPACITY * 2);
        require(failed.is_null());
        let after = ALLOCATOR.snapshot();
        require(after.failures == before.failures + 1);
        require(after.used == before.used && after.live_requested == 31 && after.live_blocks == 1);
        for i in 0..31 {
            require(shrunk.add(i).read() == i as u8);
        }
        ALLOCATOR.dealloc(shrunk, layout(31, 64));

        // Huge but valid nonzero layouts: no isize overflow or fabricated pointer.
        let huge = layout(isize::MAX as usize, 1);
        require(ALLOCATOR.alloc(huge).is_null());
        let high_alignment = layout(1, 1usize << (usize::BITS - 2));
        require(ALLOCATOR.alloc(high_alignment).is_null());

        large_probe(CAPACITY - 4096);
        // Deliberately create holes and then require coalescing into the same
        // near-capacity block that succeeded before fragmentation.
        let mut blocks = [ptr::null_mut(); 24];
        let block_layout = layout(4096, 16);
        for block in &mut blocks {
            *block = ALLOCATOR.alloc(block_layout);
            require(!block.is_null());
        }
        for i in (0..24).step_by(2) {
            ALLOCATOR.dealloc(blocks[i], block_layout);
        }
        for i in (1..24).step_by(2) {
            ALLOCATOR.dealloc(blocks[i], block_layout);
        }
    }
    ALLOCATOR.require_empty();
    large_probe(CAPACITY - 4096);
}
