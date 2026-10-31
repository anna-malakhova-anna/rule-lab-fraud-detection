# ADR-003: What a rule hit prevents, and how hits are labelled

**Decision.** When a rule fires on a fraud case, each later loss transaction in that case is prevented in
proportion to the strongest action that landed at or before it:

| Action | Share of later loss prevented | Good customer's money held |
|---|---|---|
| block | 100% | 5 days |
| hold | 100% | 2 days |
| rfi | 50% | none (asks for documents, doesn't stop the payment) |

**Labels.** A hit is `fraud_txn` if it lands on a planted transaction (a bad check, a stolen payment).
It is `fraud_account` if it lands on an account the fraudster controls: one opened for the scheme, or a
first-party fraudster after their scheme began. Everything else is `good`. That includes a BEC victim's
normal payments, because the victim is a good customer.

**Why.** Treating every action as a full stop would make a cheap RFI look as strong as a hold. 50% for an
RFI is my assumption, not a measurement: some fraudsters walk away when asked for documents, and some
answer with fakes. It lives in `config/backtest.yaml`.
