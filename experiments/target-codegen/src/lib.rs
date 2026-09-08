#![no_std]
//! Compile-only MCU code generation using public synthetic keys and randomness.
//! Automatic approval supplies no trusted consent. Never connect this experiment
//! to host transport or production key storage. See the assumptions in README.md.

use ironwood_approval::{Engine, Policy, Result, Review, Signed};
use orchard::keys::{FullViewingKey, SpendAuthorizingKey, SpendingKey};
use rand_chacha::{ChaCha20Rng, rand_core::SeedableRng};

/// Generate the real core's validation, approval and signing paths for a concrete RNG.
///
/// Runtime PCZT bytes and the returned core objects keep these paths observable.
/// This Rust entry point is for synthetic compilation only; it is not a device API.
pub fn synthetic_approval(bytes: &[u8]) -> Result<(Review, Signed)> {
    let spending_key = SpendingKey::from_bytes([0; 32]).unwrap();
    let viewing_key = FullViewingKey::from(&spending_key);
    let signing_key = SpendAuthorizingKey::from(&spending_key);
    let policy = Policy::regtest(10_000_000, 100_000)?;
    let rng = ChaCha20Rng::from_seed([42; 32]);
    let mut engine = Engine::with_rng(policy, viewing_key, rng)?;
    let review = engine.begin(bytes)?;
    // Synthetic code generation only: an actual device needs trusted UI consent.
    engine.approve(review.token())?;
    let signed = engine.sign(review.token(), &signing_key)?;
    Ok((review, signed))
}
