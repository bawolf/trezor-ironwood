import Std

/-! Structural model of the host adapter. Cryptographic validation is an explicit
boundary: begin receives its result, not an axiom asserting approval correctness.
Context.wire stands for exact bytes plus trusted policy, before hash abstraction.
No signature, consensus, display-rendering or device theorem is claimed. -/
namespace IronwoodApproval

structure Context where
  wire : List UInt8
  effects : List UInt8
  projection : List Nat
  deriving DecidableEq, Repr

structure Token where
  session : Nat
  request : Nat
  context : List UInt8
  deriving DecidableEq, Repr

structure Pending where
  token : Token
  context : Context
  approved : Bool
  deriving DecidableEq, Repr

structure State where
  session : Nat
  counter : Nat
  pending : Option Pending
  deriving DecidableEq, Repr

structure Receipt where
  token : Token
  context : Context
  deriving DecidableEq, Repr

def cancel (s : State) : State := { s with pending := none }

def beginRequest (s : State) (validated : Option Context) : State :=
  { s with counter := s.counter + 1, pending := validated.map fun c =>
      { token := ⟨s.session, s.counter + 1, c.wire⟩, context := c, approved := false } }

def approve (s : State) (token : Token) : State :=
  match s.pending with
  | none => cancel s
  | some p =>
    if p.approved = false ∧ p.token = token then
      { s with pending := some { p with approved := true } }
    else cancel s

/-- success represents completion of all upstream signing calls, not their internals. -/
def sign (s : State) (token : Token) (success : Bool) : State × Option Receipt :=
  (cancel s, match s.pending with
    | none => none
    | some p => if p.approved = true ∧ p.token = token ∧ success = true then
        some ⟨p.token, p.context⟩ else none)

theorem sign_consumes (s : State) (t : Token) (ok : Bool) :
    (sign s t ok).1.pending = none := by rfl

theorem replay_rejected (s : State) (t t' : Token) (ok ok' : Bool) :
    (sign (sign s t ok).1 t' ok').2 = none := by simp [sign, cancel]

theorem cancelled_request_cannot_sign (s : State) (t : Token) (ok : Bool) :
    (sign (cancel s) t ok).2 = none := by simp [sign, cancel]

theorem failed_sign_has_no_receipt (s : State) (t : Token) :
    (sign s t false).2 = none := by
  cases h : s.pending <;> simp [sign, h]

theorem successful_sign_preserves_approved_context
    (s : State) (t : Token) (ok : Bool) (r : Receipt)
    (h : (sign s t ok).2 = some r) :
    ∃ p, s.pending = some p ∧ p.approved = true ∧ p.token = t ∧
      r.token = p.token ∧ r.context = p.context := by
  cases hp : s.pending with
  | none => simp [sign, hp] at h
  | some p =>
    simp only [sign, hp] at h
    split at h
    next condition =>
      cases h
      exact ⟨p, rfl, condition.1, condition.2.1, rfl, rfl⟩
    next => contradiction

theorem begin_requires_fresh_approval (s : State) (c : Option Context)
    (t : Token) (ok : Bool) :
    (sign (beginRequest s c) t ok).2 = none := by
  cases c <;> simp [beginRequest, sign]

theorem malformed_replacement_cancels (s : State) (t : Token) (ok : Bool) :
    (sign (beginRequest s none) t ok).2 = none := by simp [beginRequest, sign]

theorem old_token_cannot_approve_replacement (s : State) (c : Context) (t : Token)
    (old : t.request ≤ s.counter) :
    (approve (beginRequest s (some c)) t).pending = none := by
  have mismatch : (Token.mk s.session (s.counter + 1) c.wire) ≠ t := by
    intro h
    have := congrArg Token.request h
    simp only at this
    omega
  simp [beginRequest, approve, mismatch, cancel]

theorem different_session_rejected (s : State) (c : Context) (t : Token)
    (different : s.session ≠ t.session) :
    (approve (beginRequest s (some c)) t).pending = none := by
  have mismatch : (Token.mk s.session (s.counter + 1) c.wire) ≠ t := by
    intro h
    exact different (congrArg Token.session h)
  simp [beginRequest, approve, mismatch, cancel]

/-- Successful accounting computes the fee after checking ordered subtraction.
    Natural-number truncation cannot turn an overspend into an accepted zero fee. -/
def account (inputs payments change limit cap : Nat) : Option Nat :=
  if inputs ≤ limit ∧ payments + change ≤ inputs ∧ inputs - (payments + change) ≤ cap
  then some (inputs - (payments + change)) else none

theorem accounting_conserves (i p c limit cap fee : Nat)
    (h : account i p c limit cap = some fee) :
    i = p + c + fee ∧ fee ≤ cap ∧ i ≤ limit := by
  unfold account at h
  split at h
  next bounds =>
    simp only [Option.some.injEq] at h
    omega
  next => contradiction

theorem overspend_rejected (i p c limit cap : Nat) (overspend : i < p + c) :
    account i p c limit cap = none := by
  simp [account, Nat.not_le.mpr overspend]

-- Positive witnesses ensure these operations are usable, not universally rejecting.
example : account 1000000 600000 390000 2100000000000000 100000 = some 10000 := by decide
example : let c : Context := ⟨[1,2], [3], [600000,390000,10000]⟩
    let s := beginRequest ⟨7,0,none⟩ (some c)
    let t : Token := ⟨7,1,c.wire⟩
    (sign (approve s t) t true).2 = some ⟨t,c⟩ := by decide

end IronwoodApproval
