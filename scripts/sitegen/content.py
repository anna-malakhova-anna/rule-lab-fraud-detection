"""Fixed descriptive text about each fraud type (the numbers come from the warehouse)."""
from __future__ import annotations

TYPOLOGY_TEXT = {
    "check_deposit_fraud": "Checks that will bounce are deposited by mobile, and most of the money is withdrawn before they come back. Some accounts are opened for it; some are existing customers turning to it.",
    "bec_vendor_change": "A fraudster posing as a real vendor gets the vendor's bank details changed, and the business pays its next invoice to the fraudster. The victim is a good customer.",
    "synthetic_shell": "Rings of freshly incorporated businesses applying with shared devices, phones, addresses and email domains. They are funded fast, then bust out with bad checks.",
    "money_mule": "An account collects many small payments from senders it has never seen and sweeps them out within a day or two.",
    "account_takeover": "A login from a new device, a change to the email or phone on file, a new payee, and payouts, all within hours. The owner notices days later.",
    "ach_return_fraud": "Money pulled in by ACH debit from accounts the business doesn't control, sent straight out, and returned as unauthorized days later. It starts in month 12 and was found by monitoring (INV-001).",
    "credit_bust_out": "Months of clean use of a line of credit, then round-trip money pumped through the account so the limit is raised, then the whole line drawn and wired out within hours.",
}


STAGE = {
    "check_deposit_fraud": "Payments", "bec_vendor_change": "Payments", "synthetic_shell": "Onboarding",
    "money_mule": "Account usage", "account_takeover": "Account usage", "ach_return_fraud": "Payments · emerging",
    "credit_bust_out": "Credit",
}
