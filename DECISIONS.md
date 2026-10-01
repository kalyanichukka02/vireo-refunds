# Decisions (where the brief was unclear, what I decided, and why)

| # | Question | Decision | Why / evidence |
|---|---|---|---|
| 1 | Why does the export sum to "over a crore" vs Rs 11 lakh? | Legacy Freshdesk amounts are paise: divide by 100. | Legacy/helpdesk ratio is exactly 100.0 on all 125 duplicated refund tickets; all legacy amounts divisible by 100. Naive Q1-Q3 2025 sums were 76-100x too high. |
| 2 | Duplicates | Keep the `helpdesk` copy, drop `legacy_fd`. | 638 ticket_ids appear in both systems; only refund amounts differ (the unit). Helpdesk copy is already in rupees. |
| 3 | Timezone (legacy timestamps stored in UTC, policy s9) | Bucket months by **created_at**; no shift applied. | Legacy `resolved_at` shows no negative durations and the same median resolution time as helpdesk (2.0h vs 1.8h), so no visible UTC shift. created_at is clean in both systems. 195 refund tickets resolve in a later month than they were created; reported in Notes. |
| 4 | Refunds on open/pending tickets | Included. | A refund amount was raised. Excluding them lowers recent quarters ~4-5% (115 tickets). |
| 5 | Reconciling to the helpdesk's "~Rs 11 lakh" | **Not reconciled; stated as such.** | Cleaned 2026 quarters are Rs 12.6-12.8 lakh; resolved/closed-only gives Rs ~12.2 lakh. No filter I tried gives 11. Finance should say what the helpdesk report excludes. I did not tune filters until it matched. |
| 6 | Which reason code to report | Show **both**: as coded by agents (official) and estimated (model). | GW-OTHER is 43% of refund Rs and is the dropdown's first option. The estimate is only ~66% accurate on my hand check, so it must not replace the official column. |
| 7 | AI or rules for re-coding | Free text model (no API); keyword rules kept as baseline. | v1 hand-written rules: 77.5% on agent-coded tickets (typos like "rfeund", "revverse" defeat exact keywords; "refund not received" was mis-read as lost-in-transit). Text model with character n-grams: 91.0%. No API key was available, and it costs Rs 0. |
| 8 | Confidence threshold | 0.60; below it stay GW-OTHER. | Cross-validated: 98.5% accurate on 83% coverage. Not tuned on the 40 hand labels (too few; would overfit). |
| 9 | Agent comparison | Show rate per ticket handled; warn against cross-team ranking; group by team. | Policy s6: Returns Desk refunds by design; Tier 2 is not comparable on volume. Returns Desk resolves only 26% of refund tickets (612 of 2,340; 25% of the rupees) - not "the large majority". |
| 10 | Agent on a ticket with several roster rows | Roster row valid on the ticket's date; fallback nearest. | All 11,600 tickets matched on date. |
| 11 | Business number | Refund+replacement on the same ticket (policy s5 forbids both): cost = unit cost + Rs 340. | Clear rule, no model uncertainty, 166 tickets. Compared against SLA credits (Rs 350 x 1,060 breaches) and transfers (Rs 305 x 1,091); all are ~Rs 0.6-0.7 lakh a quarter, none is a large leak. |
| 12 | Hand labels | Kept exactly as the human gave them (two typos in label text normalised to RETURN-QC-OK). Disagreements are not corrected. | The score has to reflect an independent judgement. Several disagreements look like labelling slips and would raise the score if "fixed"; that would be cheating. |

## Pushed back on / narrowed
- Did **not** produce an "agents ranked by money given away" table: it would mislead (see #9). The tab is by agent as asked, with warnings.
- Narrowed to refunds. Not examined: Priya's claim that CSAT rose 0.4 (not verified), why ticket volume doubled (Q2->Q4 2025), lot-code defects (a quick look shows some lots with ~30% refund rate; not investigated).

## Version history of the classifier (for the screen recording)
- **v1** keyword rules: 77.5% (n=1,349 agent-coded). Failures: typos; "not received" over-fires; DOA vs warranty. -> thrown away as the main method (kept as baseline).
- **v2** TF-IDF char+word n-grams + logistic regression, C=1, threshold 0.6: 91.0% overall / 98.5% where confident.
  Tried C=5 and C=20: slightly higher overall accuracy but lower accuracy when confident; kept C=1.
- **Human check** on real GW-OTHER tickets: 66% (n=29). This, not the 98.5%, is the number to quote.
