**To:** Arjun Mehta, Finance Controller  **Cc:** Priya Raman, Neha Kulkarni, Sameer Qureshi
**Re:** Refund summary for the board pack (attached: `vireo_refund_summary.xlsx`)

**Short answer.** Refunds over the 18 months from Jan 2025 to Jun 2026 total **Rs 67.1 lakh**, not "over a crore a quarter". The recent run-rate is **about Rs 12.6–12.8 lakh a quarter**. Your export was overstated by two data problems, not by agents.

**Why your export looked wrong**
1. Tickets from the old Freshdesk system store money in **paise**, so those refunds look 100 times too big. We proved this on 125 tickets that appear in both systems: the old value is exactly 100× the new one every time.
2. **638 tickets appear twice** because of the migration re-import. We kept one copy of each.
After fixing both, every table in the workbook adds up to the same Rs 67.1 lakh (three check cells show 0).

**What we could not reconcile.** Sameer's helpdesk report says "around Rs 11 lakh" a quarter; we get Rs 12.6–12.8 lakh for 2026 (about 10–15% higher). No reasonable filter closes the gap. Please ask Sameer what that report leaves out before the 24th.

**Why refunds went up.** Mostly volume. Refunds are a steady 18–23% of tickets in every month; tickets rose from about 300 a month to about 800. This supports Priya's point more than the suspicion that agents are giving more away. We did not check her CSAT figure, and we cannot tell from the data why tickets doubled.

**Who and what for**
- *By agent:* Returns Desk and Billing agents appear at the top because refunds are their job (about half and a third of their tickets end in a refund). Compare agents within a team, never across teams; the sheet shows refund rate per ticket handled for that reason. Nothing in the data singles out an agent as "giving away" money.
- *By reason:* 43% of refund rupees are coded "Goodwill / Other", but that is the first choice in the dropdown, so it is over-used. Reading the agents' notes, we estimate it is closer to 14%, with the rest mostly delayed return refunds, duplicate payments and cancellations. **This estimate is right about two times in three** on a hand check of 40 tickets, so use it as a guide, not for chargebacks. Both versions are in the workbook.

**The one clear leak.** Policy says a customer gets a refund *or* a replacement, never both. **166 tickets did both** (7% of refund tickets; 9.5% in Q1 2026), costing Rs 3.0 lakh in extra units and shipping on top of Rs 5.7 lakh refunded. They come mostly from Chat and Logistics, not the Returns Desk, so they are not "one-offs". **Target: cut this to under 1% of refund tickets, worth about Rs 0.55–0.73 lakh a quarter (≈ Rs 2.5 lakh a year).** It is modest next to Rs 12.8 lakh of refunds; SLA credits and transfers are about the same size, so there is no single big leak.

**Recommended before the 24th**
1. Use the cleaned monthly table, with the "as coded" reason column as the official one.
2. Ask Sameer to explain the Rs 11 lakh vs Rs 12.6–12.8 lakh gap.
3. Have the helpdesk block "refund + replacement" on the same ticket, and stop making GW-OTHER the default dropdown choice.

*Not covered: CSAT, handle time, repeat contacts, product-lot quality. Details and every judgement call are in `DECISIONS.md`.*
