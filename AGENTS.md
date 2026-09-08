# Trezor–Ironwood development

Read `README.md`, `docs/STATUS.md`, `docs/BACKLOG.md`, `docs/THREAT_MODEL.md`,
`docs/VERIFICATION.md`, and `ops/budget.json` before choosing work.

The user authorized this machine, this repository, and an initial total budget of
USD 300. Work toward upstreamable shielded Zcash support, Safe 7 and desktop first.
Local implementation, source downloads, builds, tests, and commits in this project
are authorized. Preserve user changes. Use branches for implementation work.

- The public repository contains research, harnesses, and reviewable experiments;
  it is not approved firmware or a wallet. Do not imply otherwise.
- Prefer existing Orchard, PCZT, Trezor, and Ironwood components. Read each
  upstream's instructions before modifying it. Do not submit PRs until its actual
  contribution requirements have been satisfied. Librustzcash requires prior
  discussion and maintainer acknowledgment; the current user has no write bypass.
- Do not send issues, PRs, comments, email, or other messages without user
  authorization for that communication. Prepare concrete proposals locally.
- Keep upstream baseline checkouts at `upstreams.lock.json` revisions and clean.
  Put experiments on separate branches/worktrees and record their base commits.
- Document assumptions before implementing key handling or signing. A host is
  untrusted. Full verification must cover the exact PCZT later approved and signed.
  Do not expose the low-level preverified signer as a generic unverified API.
- Use test seeds and synthetic transactions. Hardware flashing, factory-attestation
  changes, and transactions with real funds require a separate explicit request.
- For accepted Lean results, run warning-fatal builds and upstream axiom/census
  checks. Never resolve a failure by adding `sorry`, broadening allowed axioms,
  skipping targets, or weakening acceptance criteria. Review theorem statements
  and their relationship to the executable implementation.
- Source scans, test success, and proof elaboration are distinct evidence. Report
  exactly what ran. Record failed/partial checks and remaining trust boundaries.
- The budget is USD 300 total, not recurring. No metered paid runner is configured.
  Do not launch paid APIs/VMs or buy credits with unknown costs. Existing account
  model usage is not dollar-metered here. Do not claim the ledger caps that usage.
- Continue one bounded backlog task per scheduled turn. Run `python3 scripts/check.py
  project` first. Save progress and command evidence before ending; notify only for
  a meaningful result, failure, or required user decision. Avoid parallel coding
  workers until explicitly requested. Do not change security or spending gates to
  remove a blocker.

The checks runner locks its verification process and times out subprocess groups.
These controls do not sandbox the coding agent or guarantee a model spending cap.

AI-assisted commits use `Co-authored-by: Codex <noreply@openai.com>`.
