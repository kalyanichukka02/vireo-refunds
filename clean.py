"""Step 1 - deterministic cleaning. No AI. Every change is counted in output/clean_log.txt.

Fixes:
  1. Duplicate tickets (migration re-import): keep the 'helpdesk' copy, drop the 'legacy_fd' copy.
  2. Legacy Freshdesk money is in paise -> divide by 100 (verified: ratio is exactly 100 on all
     125 duplicated tickets that carry a refund).
  3. Joins: agent (roster row valid on ticket date), order (order_id, fallback customer+sku), product.
  4. Replacement cost = unit_cost + Rs 340 (policy s5), only where replacement_issued == 'Y'.
"""
import argparse, os
import numpy as np, pandas as pd
from common import load

REPL_SHIP = 340  # policy s5

def main(data_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    log = []
    t = load(data_dir, "tickets.csv")
    log.append(f"rows read: {len(t)}  (unique ticket_id: {t.ticket_id.nunique()})")
    for col in ["created_at", "first_response_at", "resolved_at"]:
        t[col] = pd.to_datetime(t[col])

    # 1. money unit -- done BEFORE dedupe so we can prove the 100x on duplicate pairs
    d = t[t.ticket_id.duplicated(keep=False) & t.refund_amount_inr.notna()]
    pv = d.pivot_table(index="ticket_id", columns="source_system", values="refund_amount_inr", aggfunc="first").dropna()
    ratio = (pv.legacy_fd / pv.helpdesk)
    log.append(f"paise check: {len(pv)} duplicated refund tickets, legacy/helpdesk ratio min={ratio.min():.1f} max={ratio.max():.1f}")
    assert ratio.min() == ratio.max() == 100.0, "legacy money is not exactly 100x - investigate"
    t["refund_inr"] = np.where(t.source_system == "legacy_fd", t.refund_amount_inr / 100, t.refund_amount_inr)
    log.append(f"legacy refund rows converted paise->rupees: {((t.source_system=='legacy_fd') & t.refund_inr.notna()).sum()}")

    # 2. dedupe
    t["_pri"] = (t.source_system == "helpdesk").astype(int)
    t = t.sort_values(["ticket_id", "_pri"], ascending=[True, False])
    n0 = len(t)
    t = t.drop_duplicates("ticket_id", keep="first").drop(columns="_pri").sort_values("created_at")
    log.append(f"duplicate rows dropped: {n0 - len(t)}  -> {len(t)} unique tickets")

    # 3. agent join (as-of ticket date)
    a = load(data_dir, "agents.csv", parse_dates=["from_date", "to_date"])
    m = t[["ticket_id", "agent_id", "created_at"]].merge(a, on="agent_id", how="left")
    ok = (m.from_date <= m.created_at) & (m.to_date.isna() | (m.to_date >= m.created_at))
    hit = m[ok].drop_duplicates("ticket_id")
    miss = m[~m.ticket_id.isin(hit.ticket_id)].sort_values("from_date").drop_duplicates("ticket_id", keep="last")
    ag = pd.concat([hit, miss])[["ticket_id", "name", "site", "team", "shift", "tier"]]
    ag.columns = ["ticket_id", "agent_name", "agent_site", "agent_team", "agent_shift", "agent_tier"]
    t = t.merge(ag, on="ticket_id", how="left")
    log.append(f"agent join: {len(hit)} matched on roster date, {len(miss)} fell back to nearest roster row, "
               f"{t.agent_name.isna().sum()} unmatched")

    # 4. order + product join
    o = load(data_dir, "orders.csv", parse_dates=["order_date"])
    t = t.merge(o[["order_id", "order_date", "qty", "order_value_inr", "lot_code"]], on="order_id", how="left")
    fb = o.sort_values("order_date").drop_duplicates(["customer_id", "sku"], keep="last")
    fb = fb.rename(columns={"sku": "product_sku"})[["customer_id", "product_sku", "order_date", "qty", "order_value_inr", "lot_code"]]
    need = t.order_date.isna()
    t2 = t[need][["ticket_id", "customer_id", "product_sku"]].merge(fb, on=["customer_id", "product_sku"], how="left").set_index("ticket_id")
    for c in ["order_date", "qty", "order_value_inr", "lot_code"]:
        t.loc[need, c] = t.loc[need, "ticket_id"].map(t2[c])
    log.append(f"order join: {(~need).sum()} via order_id, {need.sum() - t.order_date.isna().sum()} via customer+sku fallback, {t.order_date.isna().sum()} unmatched")
    p = load(data_dir, "products.csv")[["sku", "product_name", "family", "unit_cost_inr", "retail_price_inr", "warranty_months"]]
    t = t.merge(p, left_on="product_sku", right_on="sku", how="left").drop(columns="sku")
    t["days_since_order"] = (t.created_at.dt.normalize() - t.order_date).dt.days

    # 5. replacement cost
    t["replacement_cost_inr"] = np.where(t.replacement_issued == "Y", t.unit_cost_inr + REPL_SHIP, 0.0)
    t["is_refund"] = t.refund_inr.notna()
    t["double_remedy"] = t.is_refund & (t.replacement_issued == "Y")
    t["month"] = t.created_at.dt.to_period("M").astype(str)   # bucketed by created_at (IST) - see DECISIONS.md
    log.append(f"refund tickets: {t.is_refund.sum()}  total Rs {t.refund_inr.sum():,.0f}")
    log.append(f"refund + replacement on same ticket: {t.double_remedy.sum()}")
    t.to_csv(os.path.join(out_dir, "tickets_clean.csv"), index=False)
    open(os.path.join(out_dir, "clean_log.txt"), "w").write("\n".join(log))
    print("\n".join(log))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--data-dir", default="data"); ap.add_argument("--out-dir", default="output")
    a = ap.parse_args(); main(a.data_dir, a.out_dir)
