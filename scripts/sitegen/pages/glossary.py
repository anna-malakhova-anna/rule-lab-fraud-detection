"""The glossary page."""
from __future__ import annotations

from scripts.sitegen.components import esc, page_title


def glossary() -> str:
    terms = [
        ("RFI", "Request for information: ask the customer for documents. The payment is not stopped."),
        ("Hold", "Delay the payment, the deposited funds or the credit draw until reviewed (assumed 2 days for a good customer)."),
        ("Block", "At onboarding: decline the application. R6 declines only strong identity links at newly incorporated businesses."),
        ("Precision", "Share of alerts that landed on fraud (a fraudulent transaction or a fraudster's account)."),
        ("Recall", "Share of fraud cases (or fraud dollars) the rules caught."),
        ("Dollar-days held", "Good customers' money held × days held. $10,000 held for 2 days is 20,000 dollar-days."),
        ("Champion / challenger", "The current rule set and a proposed one, graded on the same held-out months."),
        ("Label delay", "The time between a fraud happening and the bank confirming it was fraud."),
        ("Alarm", "A week where a monitored series is far above its own recent normal."),
        ("Bust-out", "Building a clean credit history, raising the limit, then drawing everything and disappearing."),
        ("Charge-off", "The bank writing off a balance it no longer expects to collect (here, 120 days after a missed payment)."),
        ("First-party fraud", "Fraud by the customer themselves, as opposed to someone impersonating or exploiting them."),
        ("Case", "The unit an analyst works: every alert on one business on one review day."),
        ("Priority score", "What is at stake on a case times how often its rule's alerts were fraud, as known when tuning."),
        ("Lapsed case", "A case nobody reviewed in time: its hold releases and the money moves."),
        ("Reason code", "A short stable code for why a rule fired (for example CHK_OUT_FAST), used in queues and playbooks."),
    ]
    dl = "".join(f"<dt>{esc(a)}</dt><dd>{esc(b)}</dd>" for a, b in terms)
    return f"""{page_title("Glossary", "The words on these pages, in plain terms")}<div class="card"><dl>{dl}</dl></div>"""
