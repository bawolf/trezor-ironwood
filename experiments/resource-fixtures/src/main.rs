//! Synthetic fixture construction and an untimed upstream signature oracle.
use std::{env, fs, path::Path, process::ExitCode};

use orchard::ValuePool;
use pczt::{
    Pczt,
    roles::{
        signer::{Signer, SpendAuthSignature},
        verifier::{OrchardError, Verifier},
    },
};
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};

// This standalone test tool reuses the existing builders verbatim. Their unrelated
// conformance helpers are intentionally unused; no core lint policy is changed.
#[allow(dead_code)]
#[path = "../../../crates/approval/tests/common/mod.rs"]
mod common;

type Result<T> = std::result::Result<T, String>;
const FEE_CAP: u64 = 100_000;

#[derive(Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Manifest {
    height: u32,
    fee_cap: u64,
    fixtures: Vec<Fixture>,
}

#[derive(Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Fixture {
    name: String,
    sha256: String,
    byte_length: usize,
    action_count: usize,
    real_input_count: usize,
    required_signature_count: usize,
    existing_signature_count: usize,
    positive_output_count: usize,
    padding_input_count: usize,
    padding_output_count: usize,
    anchor_present: bool,
    ock_present: Vec<bool>,
    shielded_sighash: String,
}

fn debug(error: impl std::fmt::Debug) -> String {
    format!("{error:?}")
}

fn pczt_json(pczt: Pczt) -> Result<Value> {
    serde_json::to_value(pczt::v2::Pczt::try_from(pczt).map_err(debug)?).map_err(debug)
}

fn names() -> Vec<String> {
    (1..=8)
        .map(|n| format!("outputs-{n}.pczt"))
        .chain((2..=8).map(|n| format!("inputs-{n}.pczt")))
        .collect()
}

fn describe(name: &str, bytes: &[u8]) -> Result<Fixture> {
    // The normal admission/ownership/ciphertext policy applies to the originals.
    common::engine().begin(bytes).map_err(debug)?;
    let pczt = Pczt::parse(bytes).map_err(debug)?;
    let action_count = pczt.ironwood().actions().len();
    let anchor_present = pczt.ironwood().anchor().is_some();
    let digest = Signer::new(pczt.clone()).map_err(debug)?.shielded_sighash();
    let value = pczt_json(pczt)?;
    let actions = value["ironwood"]["actions"]
        .as_array()
        .ok_or("missing Ironwood actions")?;
    let mut real_inputs = 0;
    let mut positive_outputs = 0;
    let mut signatures = 0;
    for action in actions {
        let input = action["spend"]["value"]
            .as_u64()
            .ok_or("missing input value")?;
        let output = action["output"]["value"]
            .as_u64()
            .ok_or("missing output value")?;
        let signed = !action["spend"]["spend_auth_sig"].is_null();
        if signed == (input > 0) {
            return Err("original must have only dummy-spend signatures".into());
        }
        real_inputs += usize::from(input > 0);
        positive_outputs += usize::from(output > 0);
        signatures += usize::from(signed);
    }
    Ok(Fixture {
        name: name.into(),
        sha256: format!("{:x}", Sha256::digest(bytes)),
        byte_length: bytes.len(),
        action_count,
        real_input_count: real_inputs,
        required_signature_count: real_inputs,
        existing_signature_count: signatures,
        positive_output_count: positive_outputs,
        padding_input_count: action_count - real_inputs,
        padding_output_count: action_count - positive_outputs,
        anchor_present,
        ock_present: actions
            .iter()
            .map(|a| !a["output"]["ock"].is_null())
            .collect(),
        shielded_sighash: digest.iter().map(|b| format!("{b:02x}")).collect(),
    })
}

fn generate(directory: &Path) -> Result<()> {
    fs::create_dir_all(directory).map_err(debug)?;
    if fs::read_dir(directory).map_err(debug)?.next().is_some() {
        return Err("generation directory must be empty".into());
    }
    let mut fixtures = Vec::new();
    for (series, first) in [("outputs", 1), ("inputs", 2)] {
        for n in first..=8 {
            let bytes = if series == "outputs" {
                common::build_actions(n)
            } else {
                common::build_inputs(&[100_000; 8][..n])
            };
            let name = format!("{series}-{n}.pczt");
            let fixture = describe(&name, &bytes)?;
            let (inputs, outputs) = if series == "outputs" { (1, n) } else { (n, 1) };
            if (
                fixture.action_count,
                fixture.real_input_count,
                fixture.positive_output_count,
            ) != (n, inputs, outputs)
            {
                return Err(format!("{name}: unexpected builder layout: {fixture:?}"));
            }
            fs::write(directory.join(&name), bytes).map_err(debug)?;
            fixtures.push(fixture);
        }
    }
    let manifest = Manifest {
        height: common::HEIGHT,
        fee_cap: FEE_CAP,
        fixtures,
    };
    fs::write(
        directory.join("manifest.json"),
        serde_json::to_vec_pretty(&manifest).map_err(debug)?,
    )
    .map_err(debug)?;
    println!(
        "generated {} fixtures in {}",
        manifest.fixtures.len(),
        directory.display()
    );
    Ok(())
}

fn verify_pair(original: &[u8], signed: &[u8]) -> Result<usize> {
    let original = Pczt::parse(original).map_err(debug)?;
    let signed = Pczt::parse(signed).map_err(debug)?;
    let mut oracle = Signer::new(original.clone()).map_err(debug)?;
    let digest = oracle.shielded_sighash();
    if Signer::new(signed.clone())
        .map_err(debug)?
        .shielded_sighash()
        != digest
    {
        return Err("signed effect digest differs from original".into());
    }
    let mut expected = pczt_json(original)?;
    let actions = expected["ironwood"]["actions"]
        .as_array_mut()
        .ok_or("missing original Ironwood actions")?;
    if signed.ironwood().actions().len() != actions.len() {
        return Err("signed action count differs from original".into());
    }
    let mut count = 0;
    for (index, action) in actions.iter_mut().enumerate() {
        if action["spend"]["value"]
            .as_u64()
            .ok_or("missing original input value")?
            == 0
        {
            continue;
        }
        let field = &mut action["spend"]["spend_auth_sig"];
        if !field.is_null() {
            return Err(format!("original real spend {index} was already signed"));
        }
        let signature = signed.ironwood().actions()[index]
            .spend()
            .spend_auth_sig()
            .ok_or_else(|| format!("missing real-spend signature at action {index}"))?;
        // Bind the signature to its actual action index and the Ironwood pool.
        oracle
            .apply_orchard_spend_auth_signature(&SpendAuthSignature::from_parts(
                ValuePool::Ironwood,
                index,
                signature,
            ))
            .map_err(debug)?;
        *field = json!(signature.to_vec());
        count += 1;
    }
    if count == 0 {
        return Err("original has no real spends".into());
    }
    if pczt_json(signed.clone())? != expected {
        return Err("signed PCZT changed fields other than new real-spend signatures".into());
    }
    let fvk = common::keys().0;
    Verifier::new(signed)
        .with_ironwood(|bundle| -> std::result::Result<(), OrchardError<&str>> {
            bundle.verify_cross_address_restriction()?;
            for action in bundle.actions() {
                action.verify_cv_net()?;
                action.spend().verify_nullifier(Some(&fvk))?;
                action.spend().verify_rk(Some(&fvk))?;
                action.output().verify_note_commitment(action.spend())?;
                let signature = action
                    .spend()
                    .spend_auth_sig()
                    .as_ref()
                    .ok_or(OrchardError::Custom("missing spend signature"))?;
                // Includes every retained dummy signature as well as every new real signature.
                action
                    .spend()
                    .rk()
                    .verify(&digest, signature)
                    .map_err(|_| OrchardError::Custom("invalid spend signature"))?;
            }
            Ok(())
        })
        .map_err(debug)?;
    Ok(count)
}

fn verify(original_directory: &Path, signed_directory: &Path) -> Result<()> {
    let manifest: Manifest =
        serde_json::from_slice(&fs::read(original_directory.join("manifest.json")).map_err(debug)?)
            .map_err(debug)?;
    let expected_names = names();
    if manifest.height != common::HEIGHT
        || manifest.fee_cap != FEE_CAP
        || manifest.fixtures.len() != expected_names.len()
    {
        return Err("manifest must describe all 15 fixtures at the fixed test policy".into());
    }
    let mut reply_names = Vec::new();
    for entry in fs::read_dir(signed_directory).map_err(debug)? {
        let entry = entry.map_err(debug)?;
        if !entry.file_type().map_err(debug)?.is_file() {
            return Err(format!(
                "reply must be a regular file: {}",
                entry.path().display()
            ));
        }
        reply_names.push(entry.file_name());
    }
    reply_names.sort();
    let mut sorted_names: Vec<_> = expected_names
        .iter()
        .map(std::ffi::OsString::from)
        .collect();
    sorted_names.sort();
    if reply_names != sorted_names {
        return Err("signed directory must contain exactly the 15 expected PCZT files (no missing or extra replies)".into());
    }
    let mut signature_count = 0;
    for (entry, name) in manifest.fixtures.iter().zip(expected_names) {
        // Fixed names also prevent manifest paths escaping the corpus directory.
        if entry.name != name {
            return Err(format!("expected manifest fixture {name}"));
        }
        let original = fs::read(original_directory.join(&name)).map_err(debug)?;
        if describe(&name, &original)? != *entry {
            return Err(format!(
                "{name}: original bytes or facts differ from manifest"
            ));
        }
        let signed = fs::read(signed_directory.join(&name)).map_err(debug)?;
        let count = verify_pair(&original, &signed).map_err(|error| format!("{name}: {error}"))?;
        signature_count += count;
        println!("verified {name}: {count} real-spend signatures");
    }
    println!(
        "verified 15 fixtures, {signature_count} real-spend signatures; all fields and digests preserved"
    );
    Ok(())
}

fn run() -> Result<()> {
    let args: Vec<_> = env::args_os().skip(1).collect();
    match args.as_slice() {
        [command, directory] if command == "generate" => generate(Path::new(directory)),
        [command, original, signed] if command == "verify" => verify(Path::new(original), Path::new(signed)),
        _ => Err("usage: ironwood-resource-fixtures generate <directory> | verify <original-directory> <signed-directory>".into()),
    }
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("resource-fixtures: {error}");
            ExitCode::FAILURE
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn signed(bytes: &[u8]) -> Vec<u8> {
        let mut engine = common::engine();
        let review = engine.begin(bytes).unwrap();
        engine.approve(review.token()).unwrap();
        engine
            .sign(review.token(), &common::keys().1)
            .unwrap()
            .pczt
            .serialize()
            .unwrap()
    }

    #[test]
    fn directory_oracle_accepts_both_series_and_rejects_bad_replies() {
        let directory = env::temp_dir().join(format!(
            "ironwood-resource-fixtures-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
        ));
        let originals = directory.join("originals");
        let replies = directory.join("signed");
        generate(&originals).unwrap();
        fs::create_dir(&replies).unwrap();
        for name in names() {
            let bytes = fs::read(originals.join(&name)).unwrap();
            fs::write(replies.join(name), signed(&bytes)).unwrap();
        }
        verify(&originals, &replies).unwrap();

        fs::write(replies.join("extra.pczt"), b"extra reply").unwrap();
        assert!(
            verify(&originals, &replies)
                .unwrap_err()
                .contains("missing or extra")
        );
        fs::remove_file(replies.join("extra.pczt")).unwrap();
        let first = replies.join("outputs-1.pczt");
        let control = fs::read(&first).unwrap();
        fs::remove_file(&first).unwrap();
        assert!(
            verify(&originals, &replies)
                .unwrap_err()
                .contains("missing or extra")
        );
        fs::write(&first, b"not a PCZT").unwrap();
        assert!(verify(&originals, &replies).is_err());
        fs::copy(originals.join("outputs-1.pczt"), &first).unwrap();
        assert!(
            verify(&originals, &replies)
                .unwrap_err()
                .contains("missing real-spend")
        );
        let mut corrupt = common::json(&control);
        common::flip(&mut corrupt["ironwood"]["actions"][0]["spend"]["spend_auth_sig"]);
        fs::write(&first, common::encode(corrupt)).unwrap();
        assert!(verify(&originals, &replies).is_err());
        fs::write(&first, control).unwrap();
        verify(&originals, &replies).unwrap();
        fs::remove_dir_all(directory).unwrap();
    }

    #[test]
    fn unsigned_partial_and_corrupt_responses_fail_then_restored_control_passes() {
        let original = common::build_inputs(&[100_000; 2]);
        let control = signed(&original);
        assert!(
            verify_pair(&original, &original)
                .unwrap_err()
                .contains("missing real-spend")
        );
        let mut partial = common::json(&control);
        partial["ironwood"]["actions"][0]["spend"]["spend_auth_sig"] = Value::Null;
        assert!(verify_pair(&original, &common::encode(partial)).is_err());
        let mut corrupt = common::json(&control);
        common::flip(&mut corrupt["ironwood"]["actions"][0]["spend"]["spend_auth_sig"]);
        assert!(verify_pair(&original, &common::encode(corrupt)).is_err());
        assert_eq!(verify_pair(&original, &control).unwrap(), 2);
    }

    #[test]
    fn changed_metadata_and_dummy_signatures_fail() {
        let original = common::build_actions(3);
        let control = signed(&original);
        let mut changed = common::json(&control);
        changed["ironwood"]["anchor"] = json!(vec![0; 32]);
        assert!(
            verify_pair(&original, &common::encode(changed))
                .unwrap_err()
                .contains("changed fields")
        );
        let mut changed = common::json(&control);
        let dummy = changed["ironwood"]["actions"]
            .as_array()
            .unwrap()
            .iter()
            .position(|a| a["spend"]["value"] == 0)
            .unwrap();
        common::flip(&mut changed["ironwood"]["actions"][dummy]["spend"]["spend_auth_sig"]);
        let changed = common::encode(changed);
        assert!(verify_pair(&original, &changed).is_err());
        // Identical corruption on both sides bypasses the field comparison, but
        // the full upstream verifier must still reject the invalid dummy signature.
        let mut bad_original = common::json(&original);
        common::flip(&mut bad_original["ironwood"]["actions"][dummy]["spend"]["spend_auth_sig"]);
        assert!(
            verify_pair(&common::encode(bad_original), &changed)
                .unwrap_err()
                .contains("invalid spend signature")
        );
        assert_eq!(verify_pair(&original, &control).unwrap(), 1);
    }
}
