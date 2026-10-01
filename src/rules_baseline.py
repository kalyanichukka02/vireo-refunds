"""Step 2 - re-code refund reasons from free text with transparent keyword rules (free, no API).

Rules are ordered; first match wins. If nothing matches the ticket is labelled UNCLEAR and goes to
human review rather than being forced into a code.
RULES_VERSION = "v1-baseline"
"""
import re
import pandas as pd

RULES_VERSION = "v1-baseline"

RULES = [  # (code, regex) - applied to agent_notes + customer_message, lower-cased
    ("DUP-PAYMENT",  r"charged twice|double charge|duplicate (payment|txn|transaction)|amount deducted|payment debited|failed (order|ord) after payment|payment (failed|deducted)"),
    ("CANCEL",       r"cancel"),
    ("PRICE-ADJ",    r"coupon|promo|discount|price (drop|match|adjust)|offer not applied"),
    ("LOST-TRANSIT", r"not (delivered|received|rcvd)|not delivered|delivery delay|dlvry delay|lost in transit|undelivered|never arrived|raised ticket with (crr|courier)"),
    ("WTY-BUYBACK",  r"buy-?back|warranty claim|warranty buy"),
    ("RETURN-QC-OK", r"refund (pending|not credited|delay)|rfnd (pending|not credited|delay)|reverse (pickup|pkp)|pick-?up (not done|missed)|pkp (not done|missed)|wrong item|incorrect product|\barn\b|qc"),
]
HW = r"damage|dead|not (charging|turning|working|pairing|discoverable)|defect|battery|faulty|no power|case led|bud|left earbud|right earbud"
DOA_MAX_DAYS = 10   # hardware fault this soon after order ~ 'dead on arrival' (policy: within 7 days of delivery)

def classify_row(text, days_since_order):
    t = str(text).lower().replace("\\n", " ")
    for code, rx in RULES:
        if re.search(rx, t):
            return code, "rule"
    if re.search(HW, t):
        if pd.notna(days_since_order) and days_since_order <= DOA_MAX_DAYS:
            return "DOA-REPL", "hw+recent"
        return "WTY-BUYBACK", "hw+old"
    if re.search(r"goodwill|threaten|escalat|compensat", t):
        return "GW-OTHER", "goodwill-text"
    return "UNCLEAR", "none"

def apply(df):
    txt = df.agent_notes.fillna("") + " || " + df.customer_message.fillna("")
    out = [classify_row(a, d) for a, d in zip(txt, df.days_since_order)]
    df = df.copy()
    df["pred_code"] = [o[0] for o in out]
    df["pred_rule"] = [o[1] for o in out]
    return df
