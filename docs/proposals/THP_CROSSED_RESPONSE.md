# Draft: THP ACK handling discards a crossed encrypted response

Local proposal only; no issue, PR or message has been sent upstream.

In pinned desktop trezorlib, a response that arrives while the host waits for an
ACK can advance the receive sequence bit and then be discarded without decryption.
The next ciphertext fails authentication because Noise still expects the earlier
message. This breaks continued use of the channel; it is not evidence of signature
forgery, key exposure or acceptance of unauthenticated data.

Affected source: `python/src/trezorlib/thp/channel.py` at firmware revision
`7105338e3c2c1e681940e17780609881ce53126b`, SHA-256
`01aa1ae3212d7176480358805d64f6c3c9cc7be139f8fc69e1124d3df2695488`.
The source is part of the Trezor project, copyright SatoshiLabs and contributors,
licensed under LGPL-3.0. The local reproducer imports it without modifying it.

## Trigger and mechanism

1. The device sends a timeout response while the desktop application is stalled.
2. The desktop sends a late continuation before reading that timeout response.
3. While waiting for the continuation's ACK, `Channel._read_ack` reads the queued
   timeout. Its sequence bit is new, so `_read` advances `sync_bit_receive`.
4. The timeout carries the ACK for an earlier request. `_read_ack` therefore
   discards it instead of retaining it for `read_chunk` to decrypt.
5. Retransmitted copies are now sequence duplicates. A subsequent distinct
   ciphertext is delivered to Noise with the previous receive counter and raises
   `NoiseInvalidMessage('Failed authentication of message')`.

The live emulator packet trace shows byte-identical retransmissions, not repeated
encryption. No concurrent host readers were involved. A separate minimal test
using the actual pinned Channel methods and real Noise ciphers reproduces the
discard and failed decryption; its matching-ACK positive control succeeds.
The component test injects channel/workflow state and scripts receive-side packet
I/O. Its fresh Noise_NN_25519_ChaChaPoly_SHA256 handshake supplies test ciphers;
THP uses Noise_XX_25519_AESGCM_SHA256. The send path, wire framing and complete
THP handshake/pairing protocol are not exercised.

## Evidence and limits

- Real synthetic THP run: `work/emulator-transport/recovery/attempt-02/`.
  Ordinary timeout followed by GetFeatures succeeds. A late chunk triggers the
  authentication failure before another GetFeatures can be sent. All sources and
  images remained unchanged, and explicit process cleanup completed.
- Packet/source diagnosis: `work/emulator-transport/recovery/diagnosis.md`.
  This records the differing ACK bits, sequence transitions, identical retry
  ciphertexts and the distinction between observed packets and inferred counters.
- Small reproducer: `work/host-thp-regression/test_thp_crossed_response.py`.
  The preserved first version passed two tests. After Fable review, version 2
  passed three tests in 0.010 seconds, with a saved raw log: matching-ACK positive
  control; the observed timeout/duplicate/buffered-response receive sequence with
  active workflow ACK suppression; and discard with piggybacking disabled. Passing
  characterization tests reproduce current behavior; they are not a passing fix.
  Version 2 evidence is under `work/host-thp-regression/v2/`.

The observed application schedule uses explicit Session.write/read and a six-second
stall. It has not established this failure through an ordinary client call or
read-timeout/retry API sequence; that matters when assessing practical severity.
No production keys, physical device or funds were used. A separate fresh-channel
recovery assignment was blocked by an automated safety filter before execution.
Neither successful reconnect nor safe reuse of the old channel is established.

## Questions a fix must answer

First establish the intended crossed-message contract. The present evidence does
not choose between refusing an overlapping request before receive state advances
and supporting ordered delivery of crossed responses. Keeping only one response
slot cannot preserve both distinct responses observed before the application read.

If the protocol supports such crossing, the design needs an explicit bounded
buffer or backpressure policy, defined overflow failure, and ordered delivery.
The first application read may then return the earlier timeout, not the response
to the most recent write. Specify how retained messages are acknowledged when no
further host write follows. Duplicates must not consume a second cipher nonce.
Cover standalone ACK, wrong ACK bit, ACK with payload, piggybacked ACK, and the
non-piggyback firmware path. A rejected crossing must leave a defined failure
state, not silently advance sequence state while losing cipher state.

Do not add an unbounded queue, blind drain, or automatic transaction re-signing.
No fix is proposed here. Fable confirmed the receive-side mechanism and identified
gaps in the original reproducer and overly prescriptive acceptance text. Version
2 and these narrower claims address those local evidence gaps; the full normal-API
trigger, protocol contract and recovery behavior remain open. Obtain authorization
before sending this report or a PR to upstream maintainers.
