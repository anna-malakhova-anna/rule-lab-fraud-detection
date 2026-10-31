# ADR-009: The challenger stops R1 from holding payroll

**Context.** In the first Phase 1 backtest, R1 (check money out fast) held a good business's payroll about
2,500 times over 18 months, at every cutoff in its sweep. Only 3 of its payroll hits landed on a
fraudster's account. None of the planted fraud transactions is a payroll payment: deposit-fraud money goes
to new external payees or the owner's own account.

**Decision.** The challenger runs R1 on outbound payments **excluding payroll**. The champion keeps R1 as
written, so the comparison shows the effect of the change. The exclusion lives in `config/rules.yaml`
under `challenger_scope`, and R1's challenger cutoff is tuned within that narrower scope (training months
only, as in ADR-002). The sweep keeps R1-as-written too, so both curves stay visible.

**Why a scope change and not a threshold.** The threshold sweep showed payroll delays staying high at every
cutoff, because the cutoff controls how suspicious a payment must be, not which payments R1 looks at.
Tuning could not fix it.

**Risk.** A fraudster who learns that payroll is never held could route money through a fake payroll run.
The generator does not plant that pattern, so this backtest cannot measure the risk. Ways to cover it: a
separate rule on payroll recipients or amounts that are new or changed, and watching payroll-funded losses
in monitoring (Phase 2).
