#![no_std]
//! Compile-only target probe. NOT an approval validator or a signer.
//! Intentionally omits accounting, encryption, policy and consent; never expose to a host.
use orchard::keys::FullViewingKey;
use pczt::{Pczt, roles::verifier::{Verifier, OrchardError}};

#[derive(Debug)]
pub struct Error(pub &'static str);
pub type Result<T> = core::result::Result<T, Error>;
fn ensure(ok: bool, message: &'static str) -> Result<()> {
    if ok { Ok(()) } else { Err(Error(message)) }
}
// Compile the exact same bounded scanner, without copying or diverging its implementation.
#[path = "../../../crates/approval/src/wire.rs"]
pub mod wire;

/// Exercises availability of full-FVK parsing and required commitment primitives on the MCU target.
pub fn compile_probe(bytes: &[u8], fvk: &FullViewingKey) -> Result<()> {
    let h = wire::scan(bytes)?;
    // Read all fields to keep warning-fatal checks meaningful; no policy is claimed here.
    let _ = (h.version, h.group, h.branch, h.lock_time, h.expiry, h.coin_type);
    let pczt = Pczt::parse(bytes).map_err(|_| Error("parse"))?;
    Verifier::new(pczt).with_ironwood(|bundle| -> core::result::Result<(), OrchardError<()>> {
        bundle.verify_cross_address_restriction()?;
        for action in bundle.actions() {
            action.verify_cv_net()?;
            action.spend().verify_nullifier(Some(fvk))?;
            action.spend().verify_rk(Some(fvk))?;
            action.output().verify_note_commitment(action.spend())?;
        }
        Ok(())
    }).map_err(|_| Error("verification"))?;
    Ok(())
}
