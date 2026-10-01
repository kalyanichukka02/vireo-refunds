# Vireo Audio - refund summary tool

Turns the messy helpdesk export into a **monthly refund summary by reason code and by agent** that reconciles,
and flags refunds that also got a replacement (policy s5 says never both).
**Free to run: no API key, no paid calls, no internet needed.**

## Run it (clean machine)

Needs Python 3.10+.

```bash
git clone <this repo> && cd vireo-refunds
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# put the pack's CSVs in ./data  (tickets.csv, agents.csv, orders.csv, customers.csv, products.csv)
python run_all.py --data-dir data
```

Takes under a minute (about 6 s on a laptop). Output goes to `output/`:

| File | What it is |
|---|---|
| `vireo_refund_summary.xlsx` | **The board-pack file.** Sheets: Monthly (+ reconciliation), By Reason (as coded), By Reason (estimated), By Agent, Refund+Replacement, Notes, Data. Every table is live formulas over the Data sheet. |
| `clean_log.txt` | Everything the cleaner changed, with counts. |
| `validation.txt` | Accuracy of the reason-code model (and the baseline it replaced). |
| `tickets_clean.csv`, `refunds_recoded.csv` | Cleaned tickets / refund tickets with model re-coding and confidence. |
| `evidence/` (committed) | The 40-ticket blind human check (`hand_label_FILLED.csv`), validation and cleaning logs. Re-score with `python src/score_hand_labels.py evidence/hand_label_FILLED.csv` after `run_all.py`. |

The Excel is calculated by formulas: open it in Excel/LibreOffice (some previewers show blanks until it is opened and recalculated).

File names in `data/` may carry any prefix (e.g. `abc123-tickets.csv`); they are found by suffix.
Client data is **not** in this repo (`data/` and `output/` are git-ignored: it contains customer names).

## What it does

1. **`src/clean.py`** (no AI): removes 638 duplicate tickets from the migration re-import; converts legacy Freshdesk money
   from paise to rupees (asserted: exactly 100x on all 125 duplicated refund tickets); joins agent (roster row valid on the
   ticket date), order (by order_id, else customer+SKU) and product; computes replacement cost = unit cost + Rs 340.
2. **`src/classify.py`**: ~43% of refund rupees sit on `GW-OTHER`, the dropdown's first option. A small text model
   (TF-IDF character n-grams + logistic regression) trained on the ~1,350 refunds where the agent chose a real code estimates
   the true reason for GW-OTHER tickets. Below 0.60 confidence it keeps GW-OTHER instead of guessing. It never overrides a real agent code.
3. **`src/validate.py`**: 5-fold cross-validation on agent-coded tickets, versus the first-attempt keyword rules (`src/rules_baseline.py`).
4. **`src/report.py`**: builds the Excel file.

## How we know it works (and how often it doesn't)

- Cleaning: totals tie across all sheets; three in-sheet check cells equal 0; Rs 67,09,932 total refunds, 11,600 unique tickets.
- Reason model, cross-validated on agent-coded tickets (n=1,349): keyword rules 77.5% -> text model 91.0%; where confident (>=0.6) 98.5% on 83% of tickets.
- **But GW-OTHER tickets are harder.** A human (blind) hand-labelled 40 GW-OTHER tickets: the model agreed on **19 of 29 (66%, 95% CI ~47-80%)** where it acted. Treat the estimated reason as a guide, not an audit.
- Weakest codes: DOA-REPL vs WTY-BUYBACK (both hardware faults; agents use them inconsistently), WTY-BUYBACK recall ~25%.

## What is wrong / not done

- Estimated reasons are ~2/3 right on the hardest rows; n=40 labels is small and labels come from one non-expert reviewer.
- The model has never seen a clean "goodwill" example, so genuine goodwill can be pushed into another code.
- Our 2026 quarterly total (Rs ~12.6-12.8 lakh) is ~10-15% above the helpdesk's "around Rs 11 lakh"; unexplained (see `DECISIONS.md`).
- Not done on purpose: handle-time, repeat-contact costing, CSAT analysis, lot-code quality analysis, a dashboard UI.
- `clean.py` hard-codes `legacy_fd` = paise and stops (assertion) if the 100x ratio ever stops holding.

See `DECISIONS.md` for every judgement call, and `memo_to_arjun.md` for the plain-English summary.
