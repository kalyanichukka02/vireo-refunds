"""Step 3 - how do we know the classifier works, and how often is it wrong?

Test set = refund tickets where the agent chose a real code (treated as ground truth; agents are not
perfect, so true accuracy may differ slightly). 5-fold cross-validation: each ticket is predicted by a
model that never saw it. Compared with the v1 hand-written keyword rules.
Cannot be measured here: accuracy on the GW-OTHER tickets themselves (no labels) -> use output/hand_label_sample.csv.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from sklearn.model_selection import cross_val_predict, StratifiedKFold
import classify, rules_baseline

def run(path="output/tickets_clean.csv", out_dir="output"):
    df = pd.read_csv(path)
    r = df[df.is_refund].copy()
    lab = r[r.refund_reason_code != "GW-OTHER"].reset_index(drop=True)
    lines = []
    # baseline rules
    b = rules_baseline.apply(lab)
    lines.append(f"Baseline keyword rules ({rules_baseline.RULES_VERSION}): accuracy {np.mean(b.pred_code == lab.refund_reason_code):.1%} (n={len(lab)})")
    # ML cross-validated
    X = classify.build_text(lab)
    skf = StratifiedKFold(5, shuffle=True, random_state=0)
    proba = cross_val_predict(classify.make_model(), X, lab.refund_reason_code, cv=skf, method="predict_proba")
    cls = np.array(sorted(lab.refund_reason_code.unique()))
    pred, conf = cls[proba.argmax(1)], proba.max(1)
    acc = np.mean(pred == lab.refund_reason_code)
    k = conf >= classify.THRESHOLD
    lines.append(f"Text model, 5-fold CV: accuracy {acc:.1%} on all; at confidence>={classify.THRESHOLD}: "
                 f"covers {k.mean():.0%}, accuracy {np.mean(pred[k] == lab.refund_reason_code[k]):.1%}")
    lines.append(f"  => error rate ~{1-np.mean(pred[k] == lab.refund_reason_code[k]):.1%} where it acts; ~{(~k).mean():.0%} left as GW-OTHER (not confident)")
    ct = pd.crosstab(lab.refund_reason_code.rename("agent code"), pd.Series(pred, name="model"))
    lines.append("\nConfusion matrix (rows = agent code, cols = model):\n" + ct.to_string())
    per = pd.DataFrame({"precision": ct.apply(lambda c: c[c.name] / c.sum() if c.sum() else np.nan),
                        "recall": pd.Series({c: ct.loc[c, c] / ct.loc[c].sum() for c in ct.index})}).round(2)
    lines.append("\nPer-code precision/recall:\n" + per.to_string())
    out = "\n".join(lines); print(out)
    open(os.path.join(out_dir, "validation.txt"), "w").write(out)

    # apply to GW-OTHER and write a sample for hand-labelling
    rec = classify.recode(r)
    g = rec[rec.refund_reason_code == "GW-OTHER"]
    print(f"\nGW-OTHER tickets: {len(g)}; re-coded: {g.recoded.sum()} ({g.recoded.mean():.0%}); kept as GW-OTHER: {(~g.recoded).sum()}")
    print(g[g.recoded].final_code.value_counts().to_string())
    samp = g.sample(40, random_state=7)[["ticket_id", "model_code", "model_conf", "recoded", "agent_notes", "customer_message"]].copy()
    samp["YOUR_LABEL"] = ""
    samp.to_csv(os.path.join(out_dir, "hand_label_sample.csv"), index=False)
    rec.to_csv(os.path.join(out_dir, "refunds_recoded.csv"), index=False)

if __name__ == "__main__":
    run()
