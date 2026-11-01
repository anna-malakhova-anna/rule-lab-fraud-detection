# ADR-022: Vendor bake-off with three invented vendors

**Vendors** (`config/vendors.yaml`). All invented, with made-up prices and accuracy:
- Tallowmere: device risk, called at applications and new-device logins.
- Quenchwire: email and phone risk, called at applications and contact changes.
- Larchstone: business registry verification, called at applications.

**Responses** (`generator/vendors.py`, raw `vendor_*` tables). Each vendor answers every call point, or not at all
for entities it doesn't cover. Scores are drawn from the planted truth with noise. Known blind spots are built
in: a bookkeeper's shared device scores high with the device vendor, a new business email domain scores high
with the contact vendor, and the registry misses 3% of honest businesses.

**Vendors as rules.** V1 to V3 have `status: vendor`. At onboarding a vendor flag is an RFI; on a payment within
7 days of a scored login or contact change it is a hold (the escalation mechanism, ADR-015).

**Call strategies.** Each vendor is graded on top of today's rules three ways:
- every call point it supports
- onboarding only
- only when in-house signals already point at risk

The pipeline is the same grading as everything else (`models/backtest/vendors/`). Calls are counted per
strategy, and every call is paid, answered or not.

**The buying question** (`bt_vendor_bakeoff`):
- fraud dollars added on top of today's rules
- cases only the vendor caught
- extra good businesses flagged and extra reviews, priced as in ADR-008
- vendor cost, cost per dollar prevented, and the break-even price per call
- net value
- whether the vendor answers inside a payment's 500 ms budget

Buy at the call strategy with the best net value, if that net value is positive.

**Caveat.** The vendors know the planted truth, which a real vendor never does this cleanly. Whether a vendor
adds unique catches depends heavily on how much the in-house rules already cover.

**Follow-up: the decisions rest on very few cases.** `bt_vendor_bakeoff.cases_caught_earlier` counts the test-month
cases a vendor's dollars come from (caught earlier, or more fully, than today's rules manage). It is 1 to 3 per
vendor. When a generator fix in module G (ADR-025) changed a few dozen businesses, the registry vendor went from
"buy at onboarding, $19K" to a small loss, on the strength of one case. The bake-off shows how to make the decision;
the decisions themselves are not robust at this sample size. A firmer answer needs more cases: a longer window, a
larger book, or the same comparison over several generator seeds.
