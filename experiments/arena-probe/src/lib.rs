#![no_std]
#![feature(alloc_error_handler)]
//! TEST ONLY. Fixed public keys/RNG, automatic approval, no production/GC API.
extern crate alloc;
mod arena;
mod layout_tests;
mod public_table;

use alloc::vec::Vec;
use arena::{ALLOCATOR, Counts};
use core::{
    alloc::{GlobalAlloc, Layout},
    hint::black_box,
};
use ironwood_approval::{Engine, Error, Policy, Signed};
use orchard::keys::{FullViewingKey, SpendAuthorizingKey, SpendingKey};
use rand_chacha::{ChaCha20Rng, rand_core::SeedableRng};

mod exit_code {
    pub const PREINIT: i32 = 81;
    pub const DOUBLE_INIT: i32 = 82;
    pub const REENTRY: i32 = 83;
    pub const INVARIANT: i32 = 84;
    pub const PANIC: i32 = 85;
    pub const OOM: i32 = 86;
    #[cfg(not(target_os = "none"))]
    pub const PERSONALITY: i32 = 87;
    pub const TEST_FAILURE: i32 = 90;
}
mod mode {
    pub const SIGN: u32 = 0;
    pub const CANCEL: u32 = 1;
    pub const REPLACE: u32 = 2;
    pub const OOM_BEGIN: u32 = 3;
    pub const OOM_SIGN: u32 = 4;
}
mod fault {
    pub const PREINIT: u32 = 1;
    pub const DOUBLE_INIT: u32 = 2;
    pub const REENTRY: u32 = 3;
    pub const PANIC: u32 = 4;
    pub const SEALED_FREE: u32 = 5;
    pub const LATE_OWNER: u32 = 6;
}
mod status {
    pub const OK: i32 = 0;
    pub const REJECTED: i32 = 1;
    pub const OUTPUT_CAPACITY: i32 = 2;
}
const LARGE_BLOCK: usize = 64 * 1024;

// Native _Exit performs no Rust allocation, unwinding or exit callbacks. Target
// UDF is immediate undefined-instruction trapping, not a firmware fault policy.
#[cold]
#[inline(never)]
fn fail_stop(code: i32) -> ! {
    #[cfg(not(target_os = "none"))]
    {
        unsafe extern "C" {
            fn _Exit(status: i32) -> !;
        }
        unsafe { _Exit(code) }
    }
    #[cfg(all(target_os = "none", target_arch = "arm"))]
    unsafe {
        let _ = code;
        core::arch::asm!("udf #0", options(noreturn));
    }
}

fn require(condition: bool) {
    if !condition {
        fail_stop(exit_code::TEST_FAILURE)
    }
}

#[panic_handler]
fn panic(_: &core::panic::PanicInfo<'_>) -> ! {
    fail_stop(exit_code::PANIC)
}

// Prebuilt native alloc retains an EH table reference even with panic=abort.
// No foreign unwind may cross this ABI; an unexpected personality call also
// terminates. Match pinned std/sys/personality/gcc.rs's native five-argument
// ABI: c_int version/actions, u64 class, opaque exception/context, C enum status.
// This supplies no unwinding implementation or allocator fallback.
#[cfg(not(target_os = "none"))]
#[unsafe(no_mangle)]
pub extern "C" fn rust_eh_personality(
    _version: core::ffi::c_int,
    _actions: core::ffi::c_int,
    _exception_class: u64,
    _exception: *mut core::ffi::c_void,
    _context: *mut core::ffi::c_void,
) -> core::ffi::c_int {
    fail_stop(exit_code::PERSONALITY)
}

#[alloc_error_handler]
fn allocation_error(_: Layout) -> ! {
    fail_stop(exit_code::OOM)
}

#[repr(C)]
#[derive(Default)]
pub struct Report {
    pub baseline: Counts,
    pub start: Counts,
    pub phases: [Counts; 6], // input+constructor, begin, approve, sign, serialize, teardown
    pub recovery: Counts,
    pub phase_mask: usize,
    pub serialized_bytes: usize,
    pub signatures: usize,
    pub recovered_large_block: usize,
}

#[unsafe(no_mangle)]
pub extern "C" fn arena_probe_init() {
    ALLOCATOR.init();
}

#[unsafe(no_mangle)]
pub extern "C" fn arena_probe_layout_tests() {
    layout_tests::run();
}

/// Initialize only public Fp constants; no keys, input or policy are involved.
///
/// # Safety
/// The single-threaded caller supplies writable, aligned storage outside the arena.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn arena_probe_public_init(report: *mut public_table::InitReport) {
    unsafe { report.write(public_table::initialize()) };
}

/// Test-only fatal paths. PREINIT runs before arena initialization; all others
/// require it. SEALED_FREE and LATE_OWNER also require public-table initialization.
#[unsafe(no_mangle)]
pub extern "C" fn arena_probe_fault(mode: u32) -> ! {
    match mode {
        fault::PREINIT => unsafe {
            black_box(ALLOCATOR.alloc(Layout::new::<u64>()));
        },
        fault::DOUBLE_INIT => ALLOCATOR.init(),
        fault::REENTRY => ALLOCATOR.test_reentry(),
        fault::PANIC => panic!("synthetic panic injection"),
        fault::SEALED_FREE => ALLOCATOR.test_sealed_free_gate(),
        fault::LATE_OWNER => {
            let baseline = ALLOCATOR.public_baseline().unwrap();
            core::mem::forget(black_box(alloc::boxed::Box::new([0u8; 32])));
            ALLOCATOR.require_baseline(baseline);
        }
        _ => (),
    }
    fail_stop(exit_code::TEST_FAILURE)
}

/// Execute one complete synthetic lifecycle; returns 0 success, 1 rejected input,
/// 2 inadequate caller output storage. Only mode 0 exports a signed PCZT; modes
/// 1/2 test cancel/replacement; 3/4 inject OOM at begin/sign. No key/policy arguments.
///
/// # Safety
/// Single thread, initialized image, no concurrent/recursive invocation, interrupts
/// using alloc, callbacks, GC, longjmp, or transport. Input is readable for len
/// bytes, output writable for capacity bytes, and report writable/aligned. Buffers
/// are nonnull, disjoint, caller owned, outside the arena and contain no GC pointers.
/// They remain live for this whole call; C may export bytes only after success.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn arena_probe_run(
    input: *const u8,
    len: usize,
    output: *mut u8,
    capacity: usize,
    report: *mut Report,
    mode: u32,
) -> i32 {
    let baseline = ALLOCATOR
        .public_baseline()
        .unwrap_or_else(|| fail_stop(exit_code::PREINIT));
    ALLOCATOR.require_baseline(baseline);
    layout_tests::large_probe(LARGE_BLOCK);
    let start = ALLOCATOR.snapshot();
    let mut result = Report {
        baseline,
        start,
        phases: [start; 6],
        ..Report::default()
    };
    // SAFETY: this narrow C ABI's caller guarantees the documented regions.
    let source = unsafe { core::slice::from_raw_parts(input, len) };
    let staging = unsafe { core::slice::from_raw_parts_mut(output, capacity) };
    let status = execute(source, staging, &mut result, mode);
    // All request owners have dropped; only the explicitly initialized immutable
    // public table may remain. C still cannot export until this function returns.
    result.phases[5] = ALLOCATOR.snapshot();
    result.phase_mask |= 1 << 5;
    let end = result.phases[5];
    if !end.same_live(&baseline)
        || end.allocations - start.allocations != end.deallocations - start.deallocations
    {
        teardown_failure(&result);
    }
    ALLOCATOR.require_baseline(baseline);
    layout_tests::large_probe(LARGE_BLOCK);
    result.recovered_large_block = LARGE_BLOCK;
    result.recovery = ALLOCATOR.snapshot();
    unsafe { report.write(result) };
    status
}

fn execute(source: &[u8], staging: &mut [u8], report: &mut Report, mode: u32) -> i32 {
    // Admission is nonallocating and precedes the bounded owned input copy.
    if !matches!(
        mode,
        mode::SIGN | mode::CANCEL | mode::REPLACE | mode::OOM_BEGIN | mode::OOM_SIGN
    ) || ironwood_approval::wire::preflight(source).is_err()
    {
        return status::REJECTED;
    }
    let result = (|| -> ironwood_approval::Result<()> {
        let input: Vec<u8> = source.to_vec();
        let spending = SpendingKey::from_bytes([0; 32]).unwrap();
        let ask = SpendAuthorizingKey::from(&spending);
        let mut engine = Engine::with_rng(
            Policy::regtest(10_000_000, 100_000)?,
            FullViewingKey::from(&spending),
            ChaCha20Rng::from_seed([42; 32]),
        )?;
        report.phases[0] = ALLOCATOR.snapshot();
        report.phase_mask |= 1 << 0;
        if mode == mode::OOM_BEGIN {
            ALLOCATOR.deny_allocations();
        }
        let review = engine.begin(&input)?;
        report.phases[1] = ALLOCATOR.snapshot();
        report.phase_mask |= 1 << 1;
        if mode == mode::CANCEL {
            engine.cancel();
            require(engine.approve(review.token()) == Err(Error("no pending review")));
            return Ok(());
        }
        if mode == mode::REPLACE {
            let second = engine.begin(&input)?;
            require(review.token() != second.token());
            require(engine.approve(review.token()).is_err());
            // A failed stale approval cancels pending state in the accepted core;
            // replacement teardown is still required regardless of that behavior.
            black_box((&input, &review, &second, &engine));
            return Ok(());
        }
        engine.approve(review.token())?;
        report.phases[2] = ALLOCATOR.snapshot();
        report.phase_mask |= 1 << 2;
        if mode == mode::OOM_SIGN {
            ALLOCATOR.deny_allocations();
        }
        let signed = engine.sign(review.token(), &ask)?;
        report.phases[3] = ALLOCATOR.snapshot();
        report.phase_mask |= 1 << 3;
        require(&signed.token == review.token() && &signed.sighash == review.sighash());
        report.signatures = signed.signatures.len();
        let Signed {
            pczt,
            token,
            signatures,
            ..
        } = signed;
        let serialized = pczt
            .serialize()
            .map_err(|_| Error("synthetic serialization"))?;
        report.phases[4] = ALLOCATOR.snapshot();
        report.phase_mask |= 1 << 4;
        if serialized.len() > staging.len() {
            return Err(Error("synthetic output capacity"));
        }
        // All fallible signing/serialization has succeeded. Copy to C staging;
        // export is the caller's later action, after all owners below are dropped.
        staging[..serialized.len()].copy_from_slice(&serialized);
        report.serialized_bytes = serialized.len();
        black_box((&input, &review, &engine, &signatures));
        drop((serialized, token, signatures, review, engine, input));
        Ok(())
    })();
    match result {
        Ok(()) => status::OK,
        Err(Error("synthetic output capacity")) => status::OUTPUT_CAPACITY,
        Err(_) => status::REJECTED,
    }
}

/// Diagnostic metadata only, after local-owner teardown and with no heap lock.
/// The sole native driver makes stderr nonblocking before Rust initialization.
/// A failed/partial write is ignored; termination must not depend on diagnostics.
fn teardown_failure(report: &Report) -> ! {
    #[cfg(not(target_os = "none"))]
    {
        unsafe extern "C" {
            fn write(fd: i32, buffer: *const core::ffi::c_void, count: usize) -> isize;
        }
        // SAFETY: repr(C) Report consists entirely of initialized size_t fields,
        // with no padding or arena pointers; the native driver owns stderr.
        unsafe {
            write(
                2,
                (report as *const Report).cast(),
                core::mem::size_of::<Report>(),
            );
        }
    }
    #[cfg(target_os = "none")]
    let _ = report;
    fail_stop(exit_code::INVARIANT)
}
