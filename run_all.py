"""One command: python run_all.py --data-dir data   (clean -> classify/validate -> Excel)"""
import argparse, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
import clean, validate, report

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data", help="folder holding the 6 pack files (tickets.csv, agents.csv, orders.csv, customers.csv, products.csv)")
    ap.add_argument("--out-dir", default="output")
    a = ap.parse_args(); t0 = time.time()
    print("== 1/3 cleaning ==");            clean.main(a.data_dir, a.out_dir)
    print("\n== 2/3 classifier + validation =="); validate.run(os.path.join(a.out_dir, "tickets_clean.csv"), a.out_dir)
    print("\n== 3/3 Excel report ==");       report.main(a.data_dir, a.out_dir)
    print(f"\nDone in {time.time()-t0:.0f}s. Open {os.path.join(a.out_dir, 'vireo_refund_summary.xlsx')}")
