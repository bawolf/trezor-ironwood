//! Synthetic host allocation/latency probe; never a device or transport handler.
use ironwood_approval::{Engine, Error, Policy, Signed};
use orchard::keys::{FullViewingKey, SpendAuthorizingKey, SpendingKey};
use pczt::{
    Pczt,
    roles::verifier::{OrchardError, Verifier},
};
use rand_chacha::ChaCha20Rng;
use rand_core::SeedableRng;
use serde::Serialize;
use std::{
    alloc::{GlobalAlloc, Layout, System},
    cell::UnsafeCell,
    collections::BTreeMap,
    hint::{black_box, spin_loop},
    io::{self, Write},
    path::Path,
    sync::atomic::{AtomicBool, Ordering},
    time::Instant,
};

const HEIGHT: u32 = 10_000_000;
const RNG_SEED: [u8; 32] = [42; 32]; // Public test randomness, repeated deliberately.
const PHASE_NAMES: [&str; 6] = [
    "constructor",
    "begin",
    "approve",
    "sign",
    "serialize",
    "teardown",
];

#[derive(Clone, Copy, Default, Debug, Serialize)]
struct Counts {
    allocations: usize,
    reallocations: usize,
    deallocations: usize,
    failed_requests: usize,
    requested_bytes: usize,
    largest_request_bytes: usize,
    baseline_live_bytes: usize,
    peak_live_bytes: usize,
    live_bytes: usize,
    accounting_errors: usize,
}

struct CountingAllocator {
    locked: AtomicBool,
    counts: UnsafeCell<Counts>,
}

// Every access to counts, including phase resets, holds locked. The critical
// section uses only integer operations and System directly: no Rust allocation,
// formatting, unwinding, or callbacks that could reenter this allocator.
unsafe impl Sync for CountingAllocator {}

impl CountingAllocator {
    const fn new() -> Self {
        Self {
            locked: AtomicBool::new(false),
            counts: UnsafeCell::new(Counts {
                allocations: 0,
                reallocations: 0,
                deallocations: 0,
                failed_requests: 0,
                requested_bytes: 0,
                largest_request_bytes: 0,
                baseline_live_bytes: 0,
                peak_live_bytes: 0,
                live_bytes: 0,
                accounting_errors: 0,
            }),
        }
    }

    fn access<T>(&self, f: impl FnOnce(&mut Counts) -> T) -> T {
        while self
            .locked
            .compare_exchange_weak(false, true, Ordering::Acquire, Ordering::Relaxed)
            .is_err()
        {
            spin_loop();
        }
        // SAFETY: the acquire/release lock grants exclusive access.
        let result = f(unsafe { &mut *self.counts.get() });
        self.locked.store(false, Ordering::Release);
        result
    }

    fn snapshot(&self) -> Counts {
        self.access(|c| *c)
    }

    fn reset_phase(&self) {
        self.access(|c| {
            *c = Counts {
                baseline_live_bytes: c.live_bytes,
                peak_live_bytes: c.live_bytes,
                live_bytes: c.live_bytes,
                // An error must survive resets, so later checks cannot hide it.
                accounting_errors: c.accounting_errors,
                ..Counts::default()
            };
        });
    }
}

impl Counts {
    fn request(&mut self, size: usize) {
        self.requested_bytes = self.requested_bytes.saturating_add(size);
        self.largest_request_bytes = self.largest_request_bytes.max(size);
    }

    fn resize_live(&mut self, old: usize, new: usize) {
        if let Some(live) = self
            .live_bytes
            .checked_sub(old)
            .and_then(|n| n.checked_add(new))
        {
            self.live_bytes = live;
            self.peak_live_bytes = self.peak_live_bytes.max(live);
        } else {
            self.accounting_errors = self.accounting_errors.saturating_add(1);
        }
    }

    fn allocation_result(&mut self, size: usize, ptr: *mut u8) {
        if ptr.is_null() {
            self.failed_requests = self.failed_requests.saturating_add(1);
        } else {
            self.resize_live(0, size);
        }
    }

    fn reallocation_result(&mut self, old: usize, new: usize, ptr: *mut u8) {
        if ptr.is_null() {
            // The original allocation remains valid and owned on failure.
            self.failed_requests = self.failed_requests.saturating_add(1);
        } else {
            self.resize_live(old, new);
        }
    }
}

// SAFETY: forward the exact valid layouts/pointer/size to System. Zeroed
// allocations stay zeroed; failed realloc leaves the original pointer owned.
// Count requested layouts, not malloc usable size or internal realloc overlap.
unsafe impl GlobalAlloc for CountingAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        self.access(|c| {
            c.allocations = c.allocations.saturating_add(1);
            c.request(layout.size());
            let ptr = unsafe { System.alloc(layout) };
            c.allocation_result(layout.size(), ptr);
            ptr
        })
    }

    unsafe fn alloc_zeroed(&self, layout: Layout) -> *mut u8 {
        self.access(|c| {
            c.allocations = c.allocations.saturating_add(1);
            c.request(layout.size());
            let ptr = unsafe { System.alloc_zeroed(layout) };
            c.allocation_result(layout.size(), ptr);
            ptr
        })
    }

    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        self.access(|c| {
            unsafe { System.dealloc(ptr, layout) };
            c.deallocations = c.deallocations.saturating_add(1);
            c.resize_live(layout.size(), 0);
        });
    }

    unsafe fn realloc(&self, ptr: *mut u8, layout: Layout, new_size: usize) -> *mut u8 {
        self.access(|c| {
            c.reallocations = c.reallocations.saturating_add(1);
            c.request(new_size);
            let result = unsafe { System.realloc(ptr, layout, new_size) };
            c.reallocation_result(layout.size(), new_size, result);
            result
        })
    }
}

#[global_allocator]
static ALLOCATOR: CountingAllocator = CountingAllocator::new();

#[derive(Clone, Copy, Default, Serialize)]
struct Phase {
    #[serde(flatten)]
    counts: Counts,
    elapsed_ns: u128,
}

fn measure<T>(timed: bool, work: impl FnOnce() -> T) -> (T, Phase) {
    ALLOCATOR.reset_phase();
    let start = timed.then(Instant::now);
    let result = black_box(work());
    let elapsed_ns = start.map_or(0, |start| start.elapsed().as_nanos());
    let counts = ALLOCATOR.snapshot();
    assert_eq!(counts.accounting_errors, 0, "allocator accounting error");
    (result, Phase { counts, elapsed_ns })
}

struct Keys {
    fvk: FullViewingKey,
    ask: SpendAuthorizingKey,
}

impl Keys {
    fn public_test() -> Self {
        let sk = SpendingKey::from_bytes([0; 32]).unwrap();
        Self {
            fvk: FullViewingKey::from(&sk),
            ask: SpendAuthorizingKey::from(&sk),
        }
    }

    fn engine(&self) -> Engine<ChaCha20Rng> {
        Engine::with_rng(
            Policy::regtest(HEIGHT, 100_000).unwrap(),
            self.fvk.clone(),
            ChaCha20Rng::from_seed(RNG_SEED),
        )
        .unwrap()
    }
}

#[derive(Clone, Copy, Default, Serialize)]
struct Metadata {
    action_count: usize,
    signature_count: usize,
    output_count: usize,
    padding_outputs: usize,
    dummy_spends: usize,
    ock_count: usize,
    anchor_present: bool,
    #[serde(skip)]
    real_spend_mask: u8,
}

// Upstream parsing for fixture facts is deliberately outside every measured run.
fn inspect_fixture(bytes: &[u8]) -> Metadata {
    let pczt = Pczt::parse(bytes).unwrap();
    let mut metadata = Metadata {
        anchor_present: pczt.ironwood().anchor().is_some(),
        ..Metadata::default()
    };
    Verifier::new(pczt)
        .with_ironwood(|bundle| -> Result<(), OrchardError<()>> {
            metadata.action_count = bundle.actions().len();
            assert!((1..=8).contains(&metadata.action_count));
            for (index, action) in bundle.actions().iter().enumerate() {
                if action.spend().value().unwrap().inner() > 0 {
                    metadata.signature_count += 1;
                    metadata.real_spend_mask |= 1 << index;
                    assert!(action.spend().spend_auth_sig().is_none());
                } else {
                    metadata.dummy_spends += 1;
                }
                if action.output().value().unwrap().inner() > 0 {
                    metadata.output_count += 1;
                } else {
                    metadata.padding_outputs += 1;
                }
                metadata.ock_count += usize::from(action.output().ock().is_some());
            }
            Ok(())
        })
        .unwrap();
    metadata
}

#[derive(Clone, Copy, Default, Serialize)]
struct Phases {
    constructor: Phase,
    begin: Phase,
    approve: Phase,
    sign: Phase,
    serialize: Phase,
    teardown: Phase,
}

impl Phases {
    fn elapsed_ns(self) -> [u128; 6] {
        [
            self.constructor,
            self.begin,
            self.approve,
            self.sign,
            self.serialize,
            self.teardown,
        ]
        .map(|phase| phase.elapsed_ns)
    }
}

#[derive(Clone, Copy, Default, Serialize)]
struct Run {
    phases: Phases,
    input_capacity_bytes: usize,
    review_output_capacity_bytes: usize,
    process_baseline_bytes: usize,
    teardown_retained_bytes: usize,
}

// The borrowed fixture and optional representative are harness baselines. The
// owned input copy is created outside measurement and dropped inside teardown.
// No diagnostic formatting, file I/O, or independent oracle runs inside a phase.
fn run(
    keys: &Keys,
    fixture: &[u8],
    metadata: &Metadata,
    output_path: &Path,
    representative: Option<&[u8]>,
) -> (Run, [u8; 32]) {
    let timed = representative.is_some(); // One untimed warm-up writes the representative.
    let process_baseline_bytes = ALLOCATOR.snapshot().live_bytes;
    let input = fixture.to_vec();
    let input_capacity_bytes = input.capacity();
    let (mut engine, constructor) = measure(timed, || keys.engine());
    let (review, begin) = measure(timed, || engine.begin(&input).unwrap());
    let ((), approve) = measure(timed, || engine.approve(review.token()).unwrap());
    let (signed, sign) = measure(timed, || engine.sign(review.token(), &keys.ask).unwrap());

    // Inspect actual returned data, not filename parameters. These checks do not
    // allocate, but remain outside the windows to keep phase meaning simple.
    assert_eq!(&signed.token, review.token());
    assert_eq!(&signed.sighash, review.sighash());
    let actions = signed.pczt.ironwood().actions();
    assert_eq!(actions.len(), metadata.action_count);
    assert_eq!(signed.signatures.len(), metadata.signature_count);
    for (index, action) in actions.iter().enumerate() {
        assert!(action.spend().spend_auth_sig().is_some());
        let signature = signed.signatures.iter().find(|s| s.action_index() == index);
        assert_eq!(
            signature.is_some(),
            metadata.real_spend_mask & (1 << index) != 0
        );
        if let Some(signature) = signature {
            assert_eq!(
                Some(*signature.signature()),
                *action.spend().spend_auth_sig()
            );
        }
    }
    assert_eq!(review.projection().outputs.len(), metadata.output_count);
    assert_eq!(
        review.projection().padding_outputs,
        metadata.padding_outputs
    );
    let review_output_capacity_bytes = review.projection().outputs.capacity()
        * std::mem::size_of::<ironwood_approval::ReviewedOutput>();
    let sighash = signed.sighash;
    let Signed {
        token,
        sighash: _,
        signatures,
        pczt,
    } = signed;
    // Pczt::serialize consumes the PCZT. Its releases and output Vec allocations
    // belong to this explicit phase; Review and raw input still remain live.
    let (serialized, serialize) = measure(timed, || pczt.serialize().unwrap());
    if let Some(expected) = representative {
        assert_eq!(
            serialized.as_slice(),
            expected,
            "non-reproducible signed PCZT"
        );
    } else {
        std::fs::write(output_path, &serialized).unwrap();
    }
    black_box((&input, &review, &engine, &signatures));
    let ((), teardown) = measure(timed, || {
        drop((serialized, signatures, token, review, engine, input))
    });
    let teardown_retained_bytes = teardown
        .counts
        .live_bytes
        .checked_sub(process_baseline_bytes)
        .expect("teardown consumed harness baseline");
    assert_eq!(
        teardown_retained_bytes, 0,
        "retained allocation after full teardown"
    );
    (
        Run {
            phases: Phases {
                constructor,
                begin,
                approve,
                sign,
                serialize,
                teardown,
            },
            input_capacity_bytes,
            review_output_capacity_bytes,
            process_baseline_bytes,
            teardown_retained_bytes,
        },
        sighash,
    )
}

#[derive(Serialize)]
struct Case {
    name: String,
    wire_bytes: usize,
    signed_wire_bytes: usize,
    #[serde(flatten)]
    metadata: Metadata,
    sighash_hex: String,
    timing_summary_ns: BTreeMap<&'static str, TimingSummary>,
    warmup: Run,
    runs: [Run; 5],
}

#[derive(Serialize)]
struct FailureCheck {
    name: &'static str,
    #[serde(rename = "metrics")]
    phase: Phase,
    teardown_retained_bytes: usize,
}

fn failure_check(name: &'static str, work: impl FnOnce(), no_allocations: bool) -> FailureCheck {
    let baseline = ALLOCATOR.snapshot().live_bytes;
    let ((), phase) = measure(false, work);
    let retained = phase
        .counts
        .live_bytes
        .checked_sub(baseline)
        .expect("baseline lost");
    assert_eq!(retained, 0, "failure check retained allocations");
    if no_allocations {
        assert_eq!(phase.counts.allocations, 0, "admission allocated");
        assert_eq!(phase.counts.reallocations, 0, "admission reallocated");
        assert_eq!(phase.counts.deallocations, 0, "admission deallocated");
    }
    FailureCheck {
        name,
        phase,
        teardown_retained_bytes: retained,
    }
}

fn failure_checks(keys: &Keys, maximum_input: &[u8]) -> [FailureCheck; 4] {
    let cancel = failure_check(
        "max_cancel_drop",
        || {
            let mut engine = keys.engine();
            let review = engine.begin(maximum_input).unwrap();
            engine.cancel();
            assert_eq!(
                engine.approve(review.token()),
                Err(Error("no pending review"))
            );
            drop((review, engine));
        },
        false,
    );
    let replacement = failure_check(
        "max_replacement_drop",
        || {
            let mut engine = keys.engine();
            let first = engine.begin(maximum_input).unwrap();
            let second = engine.begin(maximum_input).unwrap();
            assert_ne!(first.token(), second.token());
            engine.approve(second.token()).unwrap();
            drop((first, second, engine));
        },
        false,
    );

    let oversized = vec![0; 65_537];
    let mut engine = keys.engine();
    let oversize = failure_check(
        "oversize_65537_admission",
        || {
            assert!(matches!(
                engine.begin(&oversized),
                Err(Error("PCZT byte limit"))
            ));
        },
        true,
    );

    // Build a genuine nine-action v2 encoding entirely outside measurement.
    let nine = {
        let pczt = pczt::v2::Pczt::try_from(Pczt::parse(maximum_input).unwrap()).unwrap();
        let mut value = serde_json::to_value(pczt).unwrap();
        let actions = value["ironwood"]["actions"].as_array_mut().unwrap();
        assert_eq!(actions.len(), 8);
        actions.push(actions[0].clone());
        let bytes = serde_json::from_value::<pczt::v2::Pczt>(value)
            .unwrap()
            .serialize();
        assert_eq!(Pczt::parse(&bytes).unwrap().ironwood().actions().len(), 9);
        assert!(bytes.len() <= ironwood_approval::wire::MAX_PCZT_BYTES);
        bytes
    };
    let nine_actions = failure_check(
        "nine_action_admission",
        || {
            assert!(matches!(
                engine.begin(&nine),
                Err(Error("Ironwood action limit"))
            ));
        },
        true,
    );
    drop((engine, nine, oversized));
    [cancel, replacement, oversize, nine_actions]
}

#[derive(Serialize)]
struct TimingSummary {
    first: u128,
    median: u128,
    max: u128,
}

fn timing_summary(runs: &[Run; 5]) -> BTreeMap<&'static str, TimingSummary> {
    PHASE_NAMES
        .iter()
        .enumerate()
        .map(|(i, name)| {
            let first = runs[0].phases.elapsed_ns()[i];
            let mut times = runs.map(|r| r.phases.elapsed_ns()[i]);
            times.sort_unstable();
            (
                *name,
                TimingSummary {
                    first,
                    median: times[2],
                    max: times[4],
                },
            )
        })
        .collect()
}

fn hex(bytes: &[u8]) -> String {
    use std::fmt::Write;
    let mut result = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        write!(&mut result, "{byte:02x}").unwrap();
    }
    result
}

#[derive(Serialize)]
struct Report<'a> {
    schema_version: u8,
    rng: &'static str,
    rng_seed_hex: String,
    account_seed_hex: String,
    height: u32,
    maximum_fee: u64,
    warmup_runs: usize,
    recorded_runs: usize,
    host_arch: &'static str,
    host_os: &'static str,
    pointer_bytes: usize,
    oracle_verified: bool,
    cases: &'a [Case],
    failure_checks: &'a [FailureCheck],
}

fn report(cases: &[Case], checks: &[FailureCheck]) -> io::Result<()> {
    // Reporting serialization and stdout initialization follow all measurements.
    // serde/serde_json use alloc only and add no std feature to the measured core.
    let report = Report {
        schema_version: 1,
        rng: "ChaCha20Rng",
        rng_seed_hex: hex(&RNG_SEED),
        account_seed_hex: hex(&[0; 32]),
        height: HEIGHT,
        maximum_fee: 100_000,
        warmup_runs: 1,
        recorded_runs: 5,
        host_arch: std::env::consts::ARCH,
        host_os: std::env::consts::OS,
        pointer_bytes: std::mem::size_of::<usize>(),
        oracle_verified: false,
        cases,
        failure_checks: checks,
    };
    let json = serde_json::to_vec(&report).unwrap();
    let mut out = io::stdout().lock();
    out.write_all(&json)?;
    out.write_all(b"\n")?;
    out.flush()
}

fn main() {
    let args: Vec<_> = std::env::args_os().collect();
    assert_eq!(
        args.len(),
        3,
        "usage: resource-probe <fixture-directory> <signed-output-directory>"
    );
    let fixture_dir = Path::new(&args[1]);
    let output_dir = Path::new(&args[2]);
    std::fs::create_dir_all(output_dir).unwrap();
    assert_ne!(
        std::fs::canonicalize(fixture_dir).unwrap(),
        std::fs::canonicalize(output_dir).unwrap(),
        "signed outputs must not overwrite the input directory"
    );
    let keys = Keys::public_test();
    black_box(Instant::now()); // Initialize clock support outside any phase.
    let mut cases = Vec::with_capacity(15);
    for (series, first) in [("outputs", 1), ("inputs", 2)] {
        for n in first..=8 {
            let name = format!("{series}-{n}");
            let filename = format!("{name}.pczt");
            let fixture = std::fs::read(fixture_dir.join(&filename)).unwrap();
            let output_path = output_dir.join(&filename);
            let metadata = inspect_fixture(&fixture);
            assert_eq!(metadata.action_count, n);
            assert_eq!(
                metadata.signature_count,
                if series == "outputs" { 1 } else { n }
            );
            assert_eq!(
                metadata.output_count,
                if series == "outputs" { n } else { 1 }
            );
            let (warmup, sighash) = run(&keys, &fixture, &metadata, &output_path, None);
            let representative = std::fs::read(&output_path).unwrap();
            let runs = std::array::from_fn(|_| {
                let (run, observed_sighash) = run(
                    &keys,
                    &fixture,
                    &metadata,
                    &output_path,
                    Some(&representative),
                );
                assert_eq!(observed_sighash, sighash, "digest changed between runs");
                run
            });
            cases.push(Case {
                name,
                wire_bytes: fixture.len(),
                signed_wire_bytes: representative.len(),
                metadata,
                sighash_hex: hex(&sighash),
                timing_summary_ns: timing_summary(&runs),
                warmup,
                runs,
            });
        }
    }
    let maximum_input = std::fs::read(fixture_dir.join("inputs-8.pczt")).unwrap();
    let checks = failure_checks(&keys, &maximum_input);
    report(&cases, &checks).unwrap();
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn system_forwarding_alignment_zeroing_and_carried_live_bytes() {
        let allocator = CountingAllocator::new();
        let layout = Layout::from_size_align(64, 64).unwrap();
        // SAFETY: nonzero valid layouts, matching allocator, no use after free.
        unsafe {
            let ptr = allocator.alloc_zeroed(layout);
            assert!(!ptr.is_null());
            assert_eq!(ptr as usize % 64, 0);
            assert!(std::slice::from_raw_parts(ptr, 64).iter().all(|b| *b == 0));
            ptr.write_bytes(0x5a, 64);
            allocator.reset_phase();
            let reset = allocator.snapshot();
            assert_eq!(reset.live_bytes, 64);
            assert_eq!(reset.peak_live_bytes, 64);
            assert_eq!(reset.allocations, 0);
            let grown = allocator.realloc(ptr, layout, 128);
            assert!(!grown.is_null());
            assert_eq!(grown as usize % 64, 0);
            assert!(
                std::slice::from_raw_parts(grown, 64)
                    .iter()
                    .all(|b| *b == 0x5a)
            );
            let small = allocator.realloc(grown, Layout::from_size_align(128, 64).unwrap(), 32);
            assert!(!small.is_null());
            assert_eq!(small as usize % 64, 0);
            assert!(
                std::slice::from_raw_parts(small, 32)
                    .iter()
                    .all(|b| *b == 0x5a)
            );
            let after = allocator.snapshot();
            assert_eq!(after.reallocations, 2);
            assert_eq!(after.requested_bytes, 160);
            assert_eq!(after.largest_request_bytes, 128);
            assert_eq!(after.live_bytes, 32);
            assert_eq!(after.peak_live_bytes, 128);
            allocator.reset_phase();
            allocator.dealloc(small, Layout::from_size_align(32, 64).unwrap());
            let end = allocator.snapshot();
            assert_eq!(end.deallocations, 1);
            assert_eq!(end.live_bytes, 0);
            assert_eq!(end.peak_live_bytes, 32);
            assert_eq!(end.accounting_errors, 0);
        }
    }

    #[test]
    fn null_results_preserve_existing_ownership() {
        // Deterministically exercise the exact result-accounting paths used by
        // GlobalAlloc, without provoking the process-global OOM abort handler.
        let mut counts = Counts {
            live_bytes: 64,
            peak_live_bytes: 64,
            ..Counts::default()
        };
        counts.allocation_result(128, std::ptr::null_mut());
        counts.reallocation_result(64, 256, std::ptr::null_mut());
        assert_eq!(counts.live_bytes, 64);
        assert_eq!(counts.peak_live_bytes, 64);
        assert_eq!(counts.failed_requests, 2);
        counts.resize_live(64, 0);
        assert_eq!(counts.live_bytes, 0);
        assert_eq!(counts.accounting_errors, 0);
    }

    #[test]
    fn ordinary_allocations_balance_and_accounting_errors_survive_reset() {
        let allocator = CountingAllocator::new();
        let layout = Layout::from_size_align(17, 8).unwrap();
        unsafe {
            let ptr = allocator.alloc(layout);
            assert!(!ptr.is_null());
            allocator.dealloc(ptr, layout);
        }
        let counts = allocator.snapshot();
        assert_eq!(counts.allocations, 1);
        assert_eq!(counts.deallocations, 1);
        assert_eq!(counts.requested_bytes, 17);
        assert_eq!(counts.largest_request_bytes, 17);
        assert_eq!(counts.peak_live_bytes, 17);
        assert_eq!(counts.live_bytes, 0);
        allocator.access(|c| c.resize_live(1, 0));
        allocator.reset_phase();
        assert_eq!(allocator.snapshot().accounting_errors, 1);
    }
}
