"""Scores the human hand-check: python src/score_hand_labels.py evidence/hand_label_FILLED.csv
Compares the human's label with the model's (output/refunds_recoded.csv, made by run_all.py).
Labels are used exactly as given (obvious typos of RETURN-QC-OK normalised)."""
import sys, math
import pandas as pd

def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); a = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - a) / d, (c + a) / d

path = sys.argv[1] if len(sys.argv) > 1 else "evidence/hand_label_FILLED.csv"
h = pd.read_csv(path); rec = pd.read_csv("output/refunds_recoded.csv")
m = h.merge(rec[["ticket_id", "model_code", "model_conf", "recoded"]], on="ticket_id")
m["YOUR_LABEL"] = m.YOUR_LABEL.str.strip().str.upper().replace({"RETURN-QC-QK": "RETURN-QC-OK", "RETURN-OC-OK": "RETURN-QC-OK"})
m = m[m.YOUR_LABEL != "UNSURE"]
a = m[m.recoded]; k = int((a.model_code == a.YOUR_LABEL).sum())
lo, hi = wilson(k, len(a))
print(f"labelled tickets: {len(m)}; model acted (conf>=0.6) on {len(a)}")
print(f"agreement where model acted: {k}/{len(a)} = {k/len(a):.0%}  (95% CI {lo:.0%}-{hi:.0%})")
b = m[~m.recoded]; print(f"left as GW-OTHER: {len(b)}; human also said GW-OTHER on {(b.YOUR_LABEL=='GW-OTHER').sum()}")
