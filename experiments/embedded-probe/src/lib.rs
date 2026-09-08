#![no_std]
//! Compile-only exercise of the actual portable approval core with synthetic inputs.
//! Automatically approves the review to type-check the complete API sequence.
//! This harness provides no trusted UI consent; never connect it to host transport
//! or production key storage.

use ironwood_approval::{Engine, Policy, Result, Review, Signed};
use orchard::keys::{FullViewingKey, SpendAuthorizingKey};
use rand_core::{CryptoRng, RngCore};

/// Type-check construction, full validation/review, approval and signing on the MCU target.
///
/// The caller supplies a synthetic PCZT, trusted test policy, matching synthetic
/// keys and an RNG. No RNG implementation, seed or entropy source is provided here.
/// A generic `cargo check` does not execute this function or instantiate a device RNG.
pub fn compile_probe<R: RngCore + CryptoRng>(
    bytes: &[u8],
    policy: Policy,
    fvk: FullViewingKey,
    ask: &SpendAuthorizingKey,
    rng: R,
) -> Result<(Review, Signed)> {
    let mut engine = Engine::with_rng(policy, fvk, rng)?;
    let review = engine.begin(bytes)?;
    // Synthetic compile harness only: an actual device must obtain trusted UI consent.
    engine.approve(review.token())?;
    let signed = engine.sign(review.token(), ask)?;
    Ok((review, signed))
}
