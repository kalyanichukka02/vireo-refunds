# Submission form -  answers

**1. What did you build, and what business outcome does it move? State the number and the money.**
A free, one-command tool that cleans the helpdesk export (removes 638 duplicate tickets, converts legacy paise to rupees), re-estimates the hidden reason behind "GW-OTHER" refunds from ticket text, and produces a monthly Excel of refunds by reason code and by agent that reconciles (Rs 67.1 lakh over 18 months). Business goal: cut refund-plus-replacement tickets (policy s5 violation) from 6.8% of refund tickets (9.5% at the Q1-2026 peak) to under 1%, worth about Rs 0.55-0.73 lakh a quarter (~Rs 2.5 lakh a year) in avoided replacement cost (unit cost + Rs 340). It also explains Arjun's "over a crore": a 100x paise error plus duplicates.

**2. What does one run cost, and what would a month cost at ~650 tickets/week?**
Rs 0. No paid calls: scikit-learn on a laptop CPU, ~30-60 s for all 11,600 tickets. At 650 tickets/week = ~2,800 tickets/month; refund tickets are ~20% (~560/month) and the model scores each in milliseconds. 2,800 x Rs 0 = Rs 0 per month. (If an LLM API were used instead, ~560 refund tickets x ~600 tokens = ~0.34M tokens a month, i.e. a few rupees to tens of rupees - not needed.)

**3. How do you know it works?**
Cleaning: totals tie across all sheets, check cells = 0, paise factor asserted exactly 100x on 125 pairs. Reason model: 5-fold cross-validation on 1,349 agent-coded refunds: keyword baseline 77.5% -> text model 91.0%; 98.5% on the 83% it is confident about. On the real target (GW-OTHER) I hand-labelled 40 tickets blind: model agreed on 19 of 29 where it acted (66%, 95% CI ~47-80%). It gets wrong: DOA vs WTY-BUYBACK (both hardware faults), refund-delay vs lost-in-transit wording, and tickets that mention both refund and replacement.

**4. Did you change, narrow, or push back on the client's ask?** (can only raise your score)
Yes. (a) Declined to rank agents by "money given away": Returns Desk/Billing refund by design, Tier 2 isn't comparable on volume (policy s6); I show rate per ticket handled and group by team. (b) Showed two reason columns (as coded = official; estimated = model) because the estimate is only ~66% accurate. (c) Did not force the total to match the helpdesk's "~Rs 11 lakh": ours is 10-15% higher and I said so. (d) Narrowed to refunds; dropped CSAT, handle time, lot-code analysis.

**5. What is wrong with what you are handing us?** (can only raise your score)
Estimated reasons are ~1/3 wrong on the hardest rows; only 40 hand labels from one non-expert labeller. Model has no clean "goodwill" examples. 2026 totals don't reconcile to the helpdesk's Rs 11 lakh. Months use created_at (195 refund tickets resolve in a later month). Refunds on 115 open/pending tickets are included. The paise assumption is asserted, not configurable. Agent view shows each agent's latest team. I did not verify Priya's "CSAT +0.4". No automated tests beyond built-in checks.

**6. What did you deliberately leave out, and why?**
CSAT, handle time, repeat-contact costing, SLA/transfer deep-dives, lot-code defect analysis, a dashboard UI. The ask was a reconciling refund summary; I spent the time on reconciliation and on measuring the classifier's real error rate. (Lot codes with ~30% refund rates exist and are worth a follow-up.)

**7. Anything you built or found that nobody asked for?**
The double-remedy finding (166 tickets, Rs 5.7 lakh refunded + Rs 3.0 lakh replacement cost) which contradicts "one-offs"; the finding that the refund rate is flat at 18-23% so growth is volume; the proof of the paise unit; the 43% -> ~14% GW-OTHER estimate.

**8. What did you use AI for?** 
Claude (chat assistant, code generation and analysis) for: reading the brief, planning, writing the pandas/scikit-learn/openpyxl code, analysis, and drafting docs/memo. Helped: finding the paise and duplicate issues quickly, structuring the classifier validation. Wasted/discarded: first keyword-rules classifier (77.5%), my first assumption that the double-remedy number would be large (it is ~Rs 0.6 lakh/quarter), a leftover empty column. I hand-labelled the 40-ticket check myself, without seeing model predictions. Cost: Rs 0. Screen recording: https://youtu.be/VSKfZucNdsg


**9. Public Google Drive link:** https://drive.google.com/drive/folders/1YsWxRd_cURJ-rjB5JPoSy8jrwt8LR0Tf?usp=drive_link

**10. Someone picks this up on Monday and you are unreachable - the three things they need to know.**
(1) `python run_all.py --data-dir data` rebuilds everything; the Excel in `output/` is the deliverable and its numbers tie to `tickets_clean.csv`. (2) Estimated reasons are guidance only (~66% right on GW-OTHER) - the "as coded" column is official; and the Rs 11 lakh vs Rs 12.6-12.8 lakh gap is open with Sameer. (3) Business number = refund+replacement tickets (166 in 18 months); DECISIONS.md lists every assumption.

**11. Honest hours spent:** ~4 hours

**12. GitHub repo link:** https://github.com/kalyanichukka02/vireo-refunds
