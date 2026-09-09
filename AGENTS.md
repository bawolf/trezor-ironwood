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
  a meaningful result, failure, or required user decision. Use bounded parallel
  agent assignments with disjoint write scopes; one coordinator integrates and
  verifies their work. Do not change security or spending gates to remove a blocker.

Review each proposed change twice: an adversarial correctness review using Claude Code with Fable
(`claude --model fable`), and an independent readability review.
Keep code clear, concise, and directly understandable. Prefer precise names and
small, necessary abstractions; remove unused options, redundant helpers, and
indirection without weakening validation. Record findings and their resolutions.
The user accepts a documented Opus fallback when Claude routes a Fable request
to Opus. Check the actual model in the result and record the substitution.
The user also authorizes scoped synthetic project-source reviews through the existing
Claude Code/Fable account as needed within the project budget. Record actual models
and reported usage, use bounded per-run limits, and exclude credentials/production data.
The user prefers ample Fable review budgets over small limits that interrupt useful
reviews; use a $15 allowance for substantive reviews while respecting the $300 total.
Never label a substitute review as a Fable run. These local reviews do not authorize
publishing a PR or contacting upstream maintainers.

Prepare the work for eventual Trezor review and maintenance. Follow
`docs/TREZOR_HANDOFF.md`: small upstream-shaped changes, exact source/dependency
provenance, clean-checkout reproduction, standard generation/tests/changelog,
and explicit model support. Keep the portable approval semantics shared; reuse
existing platform APIs and add abstractions only for concrete implementations.
Synthetic keys/RNG, debug commands, auto-approval and machine-local harnesses stay
in tests/experiments, outside production paths. No component is handoff-ready
while required source or fixtures exist only in ignored local directories.
This requirement does not authorize upstream communication or hardware flashing.

The checks runner locks its verification process and times out subprocess groups.
These controls do not sandbox the coding agent or guarantee a model spending cap.

AI-assisted commits use `Co-authored-by: Codex <noreply@openai.com>`.
