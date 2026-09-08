# Initial threat model — draft, not independently reviewed

## Boundary

The desktop wallet, USB/BLE transport, lightwallet server, and supplied PCZT are
untrusted with respect to spending authorization. The device must verify facts
necessary for approval using its derived keys, protocol rules, and authenticated
transaction contents. Human approval is meaningful only if the displayed facts
are bound to what is signed.

Protect spending keys, recoverability, approved recipients/values/fees, viewing-key
privacy, pool selection, and the binding between a request and its signatures.
Assume the attacker can reorder, truncate, replay, replace, and splice messages;
lie about change and derivation paths; change network identifiers; and disconnect
the device at any stage. Physical extraction and side channels need a separate
hardware assessment and are not proven safe by emulator tests.

| Property | Required evidence / attack |
| --- | --- |
| Correct recipient and value | Recompute commitment/encryption consistency; mutate one recipient, amount, memo or output and require rejection or fresh approval. Never trust a host label. |
| Correct change | Prove ownership against the selected account and derivation; adversarial host labels an external output as change. |
| Correct fee and conservation | Checked integer accounting across transparent, Sapling, Orchard and Ironwood components, including signed value balances, padding/dummy actions, overflow and hidden outputs. |
| Correct pool/network | Bind transaction version, branch ID, network context and pool; reject cross-pool signature application. Do not assume all Unified Address receivers have the same privacy behavior. |
| Verification-to-signing continuity | Verification, rendered review, approval and signing refer to an immutable PCZT/effect snapshot; substitute bytes after any boundary and require rejection. |
| v6 re-anchoring | Allow authorized anchor/proof updates that preserve the effect digest; reject any changed approved effect. Separately test final proof/consensus validity. |
| Correct request correlation | Bind session, PCZT position/digest, pool and action index; test swaps, duplicate responses, replay, unexpected signatures and partial failure. |
| Bounded resources | Bound frame sizes, action counts, recursion, memory, and verification time before allocating. Quantify limits on Safe 7 and each later device. |
| Secret handling | No seed/spending-key exports, production secrets in fixtures, or private transaction data in logs; assess randomness and signature anti-exfiltration separately. |
| Recovery and privacy | Test cancellation, disconnect/retry, restore, reorg, wrong viewing keys and logs. Require informed viewing-key export consent and on-device receive-address verification. |

## First application contract

Model states as `Received → Parsed → Verified → Reviewed → Approved → Signed`,
plus terminal `Rejected/Cancelled`. Parsing does not imply verification. Every
transition carries the same immutable signing context. Any change to approved
effects invalidates approval. An explicitly separate post-signing finalization
step may change v6 authorizing data under the protocol rules.

The experimental host state machine, exact projection and assumptions are now
specified in `APPROVAL_CONTRACT.md`, exercised with actual PCZTs and modeled in
Lean. The device transport/UI and a machine-checked refinement remain unimplemented;
see `APPROVAL_PROOFS.md` for the exact theorem boundaries.
