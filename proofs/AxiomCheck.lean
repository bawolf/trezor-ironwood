import Approval

-- Exact, observed dependencies; changes require reviewing the theorem and its proof.

/-- info: 'IronwoodApproval.sign_consumes' does not depend on any axioms -/
#guard_msgs in
#print axioms IronwoodApproval.sign_consumes

/-- info: 'IronwoodApproval.replay_rejected' depends on axioms: [propext] -/
#guard_msgs in
#print axioms IronwoodApproval.replay_rejected

/-- info: 'IronwoodApproval.cancelled_request_cannot_sign' depends on axioms: [propext] -/
#guard_msgs in
#print axioms IronwoodApproval.cancelled_request_cannot_sign

/-- info: 'IronwoodApproval.failed_sign_has_no_receipt' depends on axioms: [propext] -/
#guard_msgs in
#print axioms IronwoodApproval.failed_sign_has_no_receipt

/-- info: 'IronwoodApproval.successful_sign_preserves_approved_context' depends on axioms: [propext] -/
#guard_msgs in
#print axioms IronwoodApproval.successful_sign_preserves_approved_context

/-- info: 'IronwoodApproval.begin_requires_fresh_approval' depends on axioms: [propext] -/
#guard_msgs in
#print axioms IronwoodApproval.begin_requires_fresh_approval

/-- info: 'IronwoodApproval.malformed_replacement_cancels' depends on axioms: [propext] -/
#guard_msgs in
#print axioms IronwoodApproval.malformed_replacement_cancels

/-- info: 'IronwoodApproval.old_token_cannot_approve_replacement' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms IronwoodApproval.old_token_cannot_approve_replacement

/-- info: 'IronwoodApproval.different_session_rejected' depends on axioms: [propext] -/
#guard_msgs in
#print axioms IronwoodApproval.different_session_rejected

/-- info: 'IronwoodApproval.accounting_conserves' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms IronwoodApproval.accounting_conserves

/-- info: 'IronwoodApproval.overspend_rejected' depends on axioms: [propext] -/
#guard_msgs in
#print axioms IronwoodApproval.overspend_rejected
