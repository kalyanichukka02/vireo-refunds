"""Step 4 - board-pack workbook. All tables are live SUMIFS/COUNTIFS formulas over the 'Data' sheet,
so every total can be traced and re-checked. Run after clean.py and validate.py."""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as L
from common import load

F = "Arial"
HDR = PatternFill("solid", fgColor="1F3864"); SUB = PatternFill("solid", fgColor="D9E1F2"); WARN = PatternFill("solid", fgColor="FFF2CC")
def hdr(c): c.font = Font(name=F, bold=True, color="FFFFFF", size=10); c.fill = HDR; c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
def txt(c, bold=False, color="000000", size=10, italic=False): c.font = Font(name=F, bold=bold, color=color, size=size, italic=italic)
NUM = '#,##0;(#,##0);"-"'; PCT = '0.0%'

def main(data_dir, out_dir):
    t = pd.read_csv(os.path.join(out_dir, "tickets_clean.csv"), parse_dates=["created_at"])
    rec = pd.read_csv(os.path.join(out_dir, "refunds_recoded.csv"))
    r = t[t.is_refund].merge(rec[["ticket_id", "final_code", "model_conf"]], on="ticket_id", how="left")
    r["quarter"] = r.created_at.dt.to_period("Q").astype(str)
    r["dbl"] = r.double_remedy.astype(int)
    months = sorted(t.month.unique()); quarters = sorted(r.quarter.unique())
    codes = ["CANCEL", "DOA-REPL", "DUP-PAYMENT", "GW-OTHER", "LOST-TRANSIT", "PRICE-ADJ", "RETURN-QC-OK", "WTY-BUYBACK"]
    names = {"GW-OTHER": "Goodwill / Other (dropdown default)", "DOA-REPL": "Dead on arrival, refund chosen", "LOST-TRANSIT": "Lost or undelivered",
             "DUP-PAYMENT": "Duplicate or failed payment", "CANCEL": "Cancellation before dispatch", "PRICE-ADJ": "Price or coupon adjustment",
             "RETURN-QC-OK": "Return received, passed QC", "WTY-BUYBACK": "Warranty buy-back"}
    raw = load(data_dir, "tickets.csv"); raw["q"] = pd.to_datetime(raw.created_at).dt.to_period("Q").astype(str)
    raw_q = raw.groupby("q").refund_amount_inr.sum()

    wb = Workbook()
    # ---------------- Data
    wsD = wb.active; wsD.title = "Data"
    cols = ["ticket_id", "month", "quarter", "agent_id", "agent_name", "agent_team", "agent_tier", "refund_reason_code", "final_code",
            "refund_inr", "replacement_issued", "dbl", "replacement_cost_inr", "assigned_team", "status"]
    heads = ["Ticket", "Month", "Quarter", "Agent ID", "Agent", "Agent team", "Tier", "Reason (agent)", "Reason (estimated)",
             "Refund Rs", "Replacement?", "Refund+Repl (1/0)", "Replacement cost Rs", "First-routed team", "Status"]
    for j, h in enumerate(heads, 1): hdr(wsD.cell(1, j, h))
    for i, row in enumerate(r[cols].itertuples(index=False), 2):
        for j, v in enumerate(row, 1):
            c = wsD.cell(i, j, v); txt(c)
    N = len(r) + 1
    for j, w in enumerate([11, 9, 9, 9, 18, 20, 5, 15, 15, 11, 11, 10, 12, 20, 9], 1): wsD.column_dimensions[L(j)].width = w
    wsD.freeze_panes = "A2"
    R = lambda col: f"Data!${col}$2:${col}${N}"

    def banner(ws, text, row=1, width=12):
        ws.cell(row, 1, text); txt(ws.cell(row, 1), bold=True, size=13)

    # ---------------- Monthly (volume + refund rate)
    wsM = wb.create_sheet("Monthly", 0)
    banner(wsM, "Vireo Audio - refunds by month (Rs, de-duplicated, legacy paise converted)")
    for j, h in enumerate(["Month", "Tickets handled", "Refund tickets", "Refund Rs", "Refund rate (% of tickets)", "Avg refund Rs"], 1): hdr(wsM.cell(3, j, h))
    tc = t.groupby("month").size()
    for i, m in enumerate(months, 4):
        wsM.cell(i, 1, m); c = wsM.cell(i, 2, int(tc[m])); c.font = Font(name=F, color="0000FF", size=10)
        wsM.cell(i, 3, f"=COUNTIFS({R('B')},A{i})"); wsM.cell(i, 4, f"=SUMIFS({R('J')},{R('B')},A{i})")
        wsM.cell(i, 5, f"=IF(B{i}=0,0,C{i}/B{i})"); wsM.cell(i, 6, f"=IF(C{i}=0,0,D{i}/C{i})")
        for j in (1, 3, 4, 5, 6): txt(wsM.cell(i, j))
        for j, f in ((2, NUM), (3, NUM), (4, NUM), (5, PCT), (6, NUM)): wsM.cell(i, j).number_format = f
    e = 3 + len(months); tr = e + 1
    wsM.cell(tr, 1, "TOTAL")
    for j in (2, 3, 4): wsM.cell(tr, j, f"=SUM({L(j)}4:{L(j)}{e})")
    wsM.cell(tr, 5, f"=C{tr}/B{tr}"); wsM.cell(tr, 6, f"=D{tr}/C{tr}")
    for j in range(1, 7): txt(wsM.cell(tr, j), bold=True); wsM.cell(tr, j).fill = SUB
    for j, f in ((2, NUM), (3, NUM), (4, NUM), (5, PCT), (6, NUM)): wsM.cell(tr, j).number_format = f
    wsM.cell(tr + 2, 1, "Blue = value taken from tickets_clean.csv (all tickets, refund or not); black = formula over the Data sheet. Bucketed by ticket creation month (IST).")
    txt(wsM.cell(tr + 2, 1), italic=True, size=9)
    # reconciliation block
    rr = tr + 4
    wsM.cell(rr, 1, "Reconciliation: why the export showed 'over a crore'"); txt(wsM.cell(rr, 1), bold=True, size=11)
    for j, h in enumerate(["Quarter", "Naive sum of export (Rs)", "Cleaned total (Rs)", "Overstatement (x)"], 1): hdr(wsM.cell(rr + 1, j, h))
    for i, q in enumerate(quarters, rr + 2):
        wsM.cell(i, 1, q); c = wsM.cell(i, 2, float(raw_q[q])); c.font = Font(name=F, color="0000FF", size=10)
        wsM.cell(i, 3, f"=SUMIFS({R('J')},{R('C')},A{i})"); wsM.cell(i, 4, f"=B{i}/C{i}")
        for j in (1, 3, 4): txt(wsM.cell(i, j))
        for j, f in ((2, NUM), (3, NUM), (4, '0.0"x"')): wsM.cell(i, j).number_format = f
    wsM.cell(rr + 2 + len(quarters), 1, "Naive sum = refund_amount_inr as exported, duplicates included, legacy Freshdesk values (paise) not converted. "
             "Sameer's ~Rs 11 lakh/quarter helpdesk figure is close to, but not identical with, our cleaned figure for 2026 (see Notes).")
    txt(wsM.cell(rr + 2 + len(quarters), 1), italic=True, size=9)
    wsM.column_dimensions["A"].width = 14
    for j in range(2, 7): wsM.column_dimensions[L(j)].width = 20
    wsM.freeze_panes = "B4"

    # ---------------- By reason (two versions)
    def reason_sheet(title, col, note, warn):
        ws = wb.create_sheet(title, 1 if col == "H" else 2)
        banner(ws, note)
        if warn:
            ws.cell(2, 1, warn); txt(ws.cell(2, 1), bold=True, color="C00000", size=10); ws.cell(2, 1).fill = WARN
        hdr(ws.cell(4, 1, "Code")); hdr(ws.cell(4, 2, "Meaning"))
        for j, m in enumerate(months, 3): hdr(ws.cell(4, j, m))
        tc = 3 + len(months); hdr(ws.cell(4, tc, "TOTAL Rs")); hdr(ws.cell(4, tc + 1, "% of total"))
        for i, cd in enumerate(codes, 5):
            ws.cell(i, 1, cd); ws.cell(i, 2, names[cd]); txt(ws.cell(i, 1)); txt(ws.cell(i, 2))
            for j in range(3, tc):
                ws.cell(i, j, f"=SUMIFS({R('J')},{R(col)},$A{i},{R('B')},{L(j)}$4)"); txt(ws.cell(i, j)); ws.cell(i, j).number_format = NUM
            ws.cell(i, tc, f"=SUM(C{i}:{L(tc-1)}{i})"); ws.cell(i, tc + 1, f"={L(tc)}{i}/{L(tc)}${5+len(codes)}")
            txt(ws.cell(i, tc), bold=True); ws.cell(i, tc).number_format = NUM; txt(ws.cell(i, tc + 1)); ws.cell(i, tc + 1).number_format = PCT
        tr = 5 + len(codes); ws.cell(tr, 1, "TOTAL")
        for j in range(3, tc + 1): ws.cell(tr, j, f"=SUM({L(j)}5:{L(j)}{tr-1})")
        ws.cell(tr, tc + 1, f"=SUM({L(tc+1)}5:{L(tc+1)}{tr-1})")
        for j in range(1, tc + 2): txt(ws.cell(tr, j), bold=True); ws.cell(tr, j).fill = SUB
        for j in range(3, tc + 1): ws.cell(tr, j).number_format = NUM
        ws.cell(tr, tc + 1).number_format = PCT
        ws.cell(tr + 1, 1, "Check vs Data sheet total"); txt(ws.cell(tr + 1, 1), italic=True, size=9)
        ws.cell(tr + 1, tc, f"={L(tc)}{tr}-SUM({R('J')})"); ws.cell(tr + 1, tc).number_format = NUM; txt(ws.cell(tr + 1, tc), italic=True, size=9)
        ws.cell(tr + 2, 1, "(should be 0 - every refund rupee is in exactly one row)"); txt(ws.cell(tr + 2, 1), italic=True, size=9)
        ws.column_dimensions["A"].width = 15; ws.column_dimensions["B"].width = 32
        for j in range(3, tc + 2): ws.column_dimensions[L(j)].width = 11
        ws.freeze_panes = "C5"
    reason_sheet("By Reason (as coded)", "H", "Refund Rs by reason code and month - AS CODED BY AGENTS (official)", "Note: 'GW-OTHER' is the dropdown's first option, so it is over-used. See the next sheet for an estimate of what it hides.")
    reason_sheet("By Reason (estimated)", "I", "Refund Rs by reason code and month - ESTIMATED re-coding of GW-OTHER from ticket text",
                 "ESTIMATE, NOT AN AUDIT: on our 40-ticket hand check the model agreed with the human reviewer on ~66% of re-coded tickets (95% CI ~47-80%). Use for direction, not for charging back.")

    # ---------------- By agent
    ag = (t.sort_values("created_at").groupby("agent_id").agg(name=("agent_name", "last"), team=("agent_team", "last"), tier=("agent_tier", "last"), tickets=("ticket_id", "count")).reset_index())
    ag = ag.sort_values(["team", "agent_id"])
    ws = wb.create_sheet("By Agent", 3)
    banner(ws, "Refund Rs by agent and month (agent = who resolved the ticket)")
    ws.cell(2, 1, "Read with care: Returns Desk and Billing refund by design; Tier 2 (Escalations & Warranty) is not comparable on volume (policy s6). Compare agents within the same team only.")
    txt(ws.cell(2, 1), bold=True, color="C00000"); ws.cell(2, 1).fill = WARN
    fixed = ["Agent ID", "Agent", "Team", "Tier", "Tickets handled", "Refund tickets", "Refund % of tickets"]
    for j, h in enumerate(fixed, 1): hdr(ws.cell(4, j, h))
    for j, m in enumerate(months, 8): hdr(ws.cell(4, j, m))
    tc = 8 + len(months); hdr(ws.cell(4, tc, "TOTAL Rs")); hdr(ws.cell(4, tc + 1, "Rs per ticket handled"))
    for i, a in enumerate(ag.itertuples(index=False), 5):
        ws.cell(i, 1, a.agent_id); ws.cell(i, 2, a.name); ws.cell(i, 3, a.team); ws.cell(i, 4, int(a.tier))
        c = ws.cell(i, 5, int(a.tickets)); c.font = Font(name=F, color="0000FF", size=10)
        ws.cell(i, 6, f"=COUNTIFS({R('D')},$A{i})"); ws.cell(i, 7, f"=IF(E{i}=0,0,F{i}/E{i})")
        for j in (1, 2, 3, 4, 6, 7): txt(ws.cell(i, j))
        ws.cell(i, 7).number_format = PCT
        for j in range(8, tc):
            ws.cell(i, j, f"=SUMIFS({R('J')},{R('D')},$A{i},{R('B')},{L(j)}$4)"); txt(ws.cell(i, j)); ws.cell(i, j).number_format = NUM
        ws.cell(i, tc, f"=SUM(H{i}:{L(tc-1)}{i})"); txt(ws.cell(i, tc), bold=True); ws.cell(i, tc).number_format = NUM
        ws.cell(i, tc + 1, f"=IF(E{i}=0,0,{L(tc)}{i}/E{i})"); txt(ws.cell(i, tc + 1)); ws.cell(i, tc + 1).number_format = NUM
    last = 4 + len(ag); tr = last + 1
    ws.cell(tr, 1, "TOTAL")
    for j in [5, 6] + list(range(8, tc + 1)): ws.cell(tr, j, f"=SUM({L(j)}5:{L(j)}{last})")
    ws.cell(tr, 7, f"=F{tr}/E{tr}"); ws.cell(tr, tc + 1, f"={L(tc)}{tr}/E{tr}")
    for j in range(1, tc + 2): txt(ws.cell(tr, j), bold=True); ws.cell(tr, j).fill = SUB
    for j in [5, 6] + list(range(8, tc + 1)) + [tc + 1]: ws.cell(tr, j).number_format = NUM
    ws.cell(tr, 7).number_format = PCT
    ws.cell(tr + 1, 1, "Check vs Data sheet total"); txt(ws.cell(tr + 1, 1), italic=True, size=9)
    ws.cell(tr + 1, tc, f"={L(tc)}{tr}-SUM({R('J')})"); ws.cell(tr + 1, tc).number_format = NUM; txt(ws.cell(tr + 1, tc), italic=True, size=9)
    ws.cell(tr + 2, 1, "Agent shown with their most recent team/tier. 'Tickets handled' (blue) comes from tickets_clean.csv."); txt(ws.cell(tr + 2, 1), italic=True, size=9)
    for j, w in enumerate([9, 18, 22, 5, 9, 9, 10], 1): ws.column_dimensions[L(j)].width = w
    for j in range(8, tc + 2): ws.column_dimensions[L(j)].width = 10
    ws.column_dimensions[L(tc)].width = 12; ws.column_dimensions[L(tc + 1)].width = 12
    ws.row_dimensions[4].height = 42; ws.freeze_panes = "H5"

    # ---------------- Refund + replacement
    wd = wb.create_sheet("Refund+Replacement", 4)
    banner(wd, "Refund AND replacement on the same ticket (policy s5 forbids both)")
    for j, h in enumerate(["Quarter", "Refund tickets", "Refund+replacement tickets", "% of refund tickets", "Refund Rs on those", "Replacement cost Rs (unit cost + Rs 340)"], 1): hdr(wd.cell(3, j, h))
    for i, q in enumerate(quarters, 4):
        wd.cell(i, 1, q); wd.cell(i, 2, f"=COUNTIFS({R('C')},A{i})"); wd.cell(i, 3, f"=SUMIFS({R('L')},{R('C')},A{i})")
        wd.cell(i, 4, f"=C{i}/B{i}"); wd.cell(i, 5, f"=SUMIFS({R('J')},{R('C')},A{i},{R('L')},1)"); wd.cell(i, 6, f"=SUMIFS({R('M')},{R('C')},A{i})")
        for j in range(1, 7): txt(wd.cell(i, j))
        for j, f in ((2, NUM), (3, NUM), (4, PCT), (5, NUM), (6, NUM)): wd.cell(i, j).number_format = f
    tr = 4 + len(quarters); wd.cell(tr, 1, "TOTAL")
    for j in (2, 3, 5, 6): wd.cell(tr, j, f"=SUM({L(j)}4:{L(j)}{tr-1})")
    wd.cell(tr, 4, f"=C{tr}/B{tr}")
    for j in range(1, 7): txt(wd.cell(tr, j), bold=True); wd.cell(tr, j).fill = SUB
    for j, f in ((2, NUM), (3, NUM), (4, PCT), (5, NUM), (6, NUM)): wd.cell(tr, j).number_format = f
    k = tr + 2; wd.cell(k, 1, "By team that FIRST routed the ticket"); txt(wd.cell(k, 1), bold=True, size=11)
    for j, h in enumerate(["Team", "Refund tickets", "Refund+replacement", "% of its refunds"], 1): hdr(wd.cell(k + 1, j, h))
    for i, tm in enumerate(sorted(r.assigned_team.unique()), k + 2):
        wd.cell(i, 1, tm); wd.cell(i, 2, f"=COUNTIFS({R('N')},A{i})"); wd.cell(i, 3, f"=SUMIFS({R('L')},{R('N')},A{i})"); wd.cell(i, 4, f"=IF(B{i}=0,0,C{i}/B{i})")
        for j in range(1, 5): txt(wd.cell(i, j))
        wd.cell(i, 4).number_format = PCT
    kk = k + 2 + r.assigned_team.nunique() + 1
    wd.cell(kk, 1, "Replacement cost = products.unit_cost_inr + Rs 340 (policy s5); refurbishment recovery not assumed. Flag is replacement_issued = 'Y' on a ticket that also has a refund."); txt(wd.cell(kk, 1), italic=True, size=9)
    wd.column_dimensions["A"].width = 26
    for j in range(2, 7): wd.column_dimensions[L(j)].width = 22

    # ---------------- Notes
    wn = wb.create_sheet("Notes", 5)
    lines = ["Assumptions and known issues", "",
        "1. Legacy (Freshdesk) refund amounts are in paise: divided by 100. Proven on 125 duplicated tickets where legacy = exactly 100 x helpdesk.",
        "2. 638 tickets were exported twice (migration re-import). The helpdesk copy is kept, the legacy copy dropped.",
        "3. Months use ticket CREATION time (IST). Legacy resolved_at showed no evidence of a UTC shift, but created_at is clean in both systems. 195 refund tickets resolve in a later month than they were created.",
        "4. Refunds on tickets still open/pending (115) are INCLUDED: the refund was raised. Excluding them lowers recent quarters by ~4-5%.",
        "5. Reconciliation gap: our 2026 quarterly totals (Rs ~12.6-12.8 lakh) are ~10-15% above the helpdesk's 'around Rs 11 lakh'. We could not explain the gap from the data (resolved/closed-only gets Rs ~12.2 lakh). Finance should confirm what the helpdesk report excludes.",
        "6. 'Reason (as coded)' is what agents chose. 'Reason (estimated)' re-codes GW-OTHER tickets from the notes with a text model; confidence < 0.6 stays GW-OTHER. Accuracy on a 40-ticket hand check: 66% of re-codes agreed (n=29). Weakest: DOA-REPL vs WTY-BUYBACK.",
        "7. Agent totals are not a ranking. Returns Desk and Billing handle refunds by design; Tier 2 is measured on resolution time, not volume.",
        "8. Refund RATE (refund tickets / tickets) is ~18-23% in every month: the growth in refund Rs comes mainly from more tickets, not more refunds per ticket."]
    for i, s in enumerate(lines, 1):
        wn.cell(i, 1, s); txt(wn.cell(i, 1), bold=(i == 1), size=12 if i == 1 else 10); wn.cell(i, 1).alignment = Alignment(wrap_text=True, vertical="top")
    wn.column_dimensions["A"].width = 150
    for ws_ in wb.worksheets:
        ws_.sheet_view.showGridLines = False if ws_.title != "Data" else True
    wb.move_sheet("Notes", offset=0)
    p = os.path.join(out_dir, "vireo_refund_summary.xlsx"); wb.save(p); print("saved", p)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--data-dir", default="data"); ap.add_argument("--out-dir", default="output")
    a = ap.parse_args(); main(a.data_dir, a.out_dir)
