# ADR-012: Phase 2 fraud types, their look-alikes, and the decline cost

Parameters are in `config/generation.yaml`. Each module's docstring describes its scheme.

**Shell rings** (`synthetic_shell.py`): 3 to 8 applicants per ring. Members share two devices, two phones, one
address and a business email domain. Each was incorporated 5 to 90 days before applying. A few ring
applications are already declined by the bank's existing checks. Each shell is funded fast from outside, then
busts out with bad checks sized to 15% of the revenue it claimed.
*Legitimate sharing:*
- 3% of owners run a second business (sharing everything)
- 5% apply through a bookkeeper's device
- 6% use a co-working address
- free-mail domains link nobody

**Mules** (`money_mule.py`): 15 to 80 payments from first-time senders over 1 to 4 weeks, swept out every 1 to
3 days. 70% are accounts opened for the purpose; 30% are existing businesses that lend their account. The loss counted
is the swept amount (the bank's exposure to recalls and reimbursement).
*Look-alike:* marketplace sellers with hundreds of small transfers and a weekly sweep to the owner.

**Account takeover** (`account_takeover.py`), all within hours:
1. a login from a new device
2. an email change (and a phone change in 60% of cases)
3. a new external payee
4. 1 to 3 payouts

The owner notices 0.5 to 5 days later.
*Look-alikes:* new phones (0.4 per owner per year), and the new-bookkeeper archetype (new device, new
email and new payees in one week).

**Decline cost: $300 per good applicant turned away.** This is invented. It stands in for lost lifetime value
and is used only to choose R6's cutoff. **It drives R6 to its loosest cutoff (any one shared attribute).** At
that cutoff R6 declines good applicants who merely share a bookkeeper's device or a co-working address. That
is a cost assumption to revisit, not a property of the data.

**Superseded in part by ADR-015:** R6 now declines only strong links and sends weaker links to an RFI.
