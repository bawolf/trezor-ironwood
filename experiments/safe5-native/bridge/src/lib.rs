#![no_std]
//! Emulator-only PCZT bridge. No host-supplied key, RNG, policy or approval.
use core::{ptr, slice};
use ironwood_approval::wire::MAX_PCZT_BYTES;
use ironwood_approval::{Engine, OutputKind, Policy, Review};
use orchard::keys::{FullViewingKey, SpendAuthorizingKey, SpendingKey};
use rand_chacha::{ChaCha20Rng, rand_core::SeedableRng};
use spin::Mutex;

pub const RESPONSE_CAPACITY: usize = 65_536;
pub const OK: i32 = 0;
pub const REJECTED: i32 = 1;
pub const OUTPUT_CAPACITY: i32 = 2;

#[repr(C)]
#[derive(Clone, Copy)]
pub struct Output {
    pub value: u64,
    pub action_index: u32,
    pub kind: u8, // 0 payment, 1 internal change.
    pub receiver: [u8; 43],
}

impl Default for Output {
    fn default() -> Self {
        Self {
            value: 0,
            action_index: 0,
            kind: 0,
            receiver: [0; 43],
        }
    }
}

#[repr(C)]
#[derive(Default)]
pub struct Snapshot {
    pub total_input: u64,
    pub payments: u64,
    pub change: u64,
    pub fee: u64,
    pub branch: u32,
    pub expiry: u32,
    pub padding_outputs: u32,
    pub output_count: u32,
    pub token: [u8; 32],
    pub outputs: [Output; 8],
}

struct State {
    engine: Engine<ChaCha20Rng>,
    ask: SpendAuthorizingKey,
    review: Option<Review>,
}

// C calls only from the trusted MicroPython executor. Reentry is a fatal
// integration error. Never hold this guard across a MicroPython call/exception.
static STATE: Mutex<Option<State>> = Mutex::new(None);

fn cancel(state: &mut State) {
    state.review = None;
    state.engine.cancel();
}

/// Validate caller-supplied synthetic PCZT bytes, invalidating any prior review.
///
/// # Safety
/// C supplies readable `length` bytes and writable, aligned Snapshot storage.
/// The buffers are disjoint and outside the Rust arena; input stays unchanged
/// until this call returns. No input pointer is retained.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn ironwood_test_begin(
    pczt: *const u8,
    length: usize,
    snapshot: *mut Snapshot,
) -> i32 {
    let mut state = STATE.try_lock().expect("bridge reentry");
    if let Some(state) = state.as_mut() {
        cancel(state);
    }
    if pczt.is_null() || length == 0 || length > MAX_PCZT_BYTES || snapshot.is_null() {
        return REJECTED;
    }
    if state.is_none() {
        let spending = SpendingKey::from_bytes([0; 32]).expect("fixed test key");
        *state = Some(State {
            engine: Engine::with_rng(
                Policy::regtest(10_000_000, 100_000).expect("fixed test policy"),
                FullViewingKey::from(&spending),
                ChaCha20Rng::from_seed([42; 32]),
            )
            .expect("fixed test RNG"),
            ask: SpendAuthorizingKey::from(&spending),
            review: None,
        });
    }
    let state = state.as_mut().expect("initialized above");
    let bytes = unsafe { slice::from_raw_parts(pczt, length) };
    let Ok(review) = state.engine.begin(bytes) else {
        return REJECTED;
    };
    let projection = review.projection();
    if projection.outputs.len() > 8 {
        cancel(state);
        return REJECTED;
    }
    let mut result = Snapshot {
        total_input: projection.total_input,
        payments: projection.payments,
        change: projection.change,
        fee: projection.fee,
        branch: projection.branch,
        expiry: projection.expiry,
        padding_outputs: projection.padding_outputs as u32,
        output_count: projection.outputs.len() as u32,
        token: *review.token().context(),
        ..Snapshot::default()
    };
    for (output, reviewed) in result.outputs.iter_mut().zip(&projection.outputs) {
        *output = Output {
            value: reviewed.value,
            action_index: reviewed.action_index as u32,
            kind: match reviewed.kind {
                OutputKind::Payment => 0,
                OutputKind::InternalChange => 1,
            },
            receiver: reviewed.receiver,
        };
    }
    state.review = Some(review);
    unsafe { snapshot.write(result) };
    OK
}

/// Called only after the trusted UI finishes its final confirmation.
/// Every attempt consumes the pending review, including wrong-token/capacity errors.
///
/// # Safety
/// C supplies a readable 32-byte token, writable output of `capacity` bytes,
/// and writable aligned `written`, all disjoint and outside the Rust arena.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn ironwood_test_sign(
    token: *const u8,
    output: *mut u8,
    capacity: usize,
    written: *mut usize,
) -> i32 {
    let mut state = STATE.try_lock().expect("bridge reentry");
    if !written.is_null() {
        unsafe { written.write(0) };
    }
    let Some(state) = state.as_mut() else {
        return REJECTED;
    };
    let Some(review) = state.review.take() else {
        state.engine.cancel();
        return REJECTED;
    };
    if token.is_null() || output.is_null() || written.is_null() || capacity > RESPONSE_CAPACITY {
        state.engine.cancel();
        return REJECTED;
    }
    let token = unsafe { &*token.cast::<[u8; 32]>() };
    if token != review.token().context() {
        state.engine.cancel();
        return REJECTED;
    }
    if state.engine.approve(review.token()).is_err() {
        return REJECTED;
    }
    let Ok(signed) = state.engine.sign(review.token(), &state.ask) else {
        return REJECTED;
    };
    let Ok(bytes) = signed.pczt.serialize() else {
        return REJECTED;
    };
    if bytes.len() > capacity {
        return OUTPUT_CAPACITY;
    }
    unsafe {
        ptr::copy_nonoverlapping(bytes.as_ptr(), output, bytes.len());
        written.write(bytes.len());
    }
    OK
}

#[unsafe(no_mangle)]
pub extern "C" fn ironwood_test_cancel() {
    let mut state = STATE.try_lock().expect("bridge reentry");
    if let Some(state) = state.as_mut() {
        cancel(state);
    }
}
