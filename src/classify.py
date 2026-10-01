"""Step 2 - re-code refund reasons from free text. Free: no API, runs in seconds on a laptop.

Idea: agents who picked a real reason code (not the dropdown default GW-OTHER) give us ~1,350 labelled
examples. Train a small text model on (agent_notes + customer_message + days-since-order bucket) and
use it to re-code tickets the agent left on GW-OTHER.

  * char n-grams  -> robust to typos ('rfeund', 'revverse', 'aftre payment' are common in the notes)
  * confidence >= THRESHOLD -> take the model's code (column `final_code`)
  * confidence <  THRESHOLD -> keep GW-OTHER (we can't tell, so we don't pretend to)
  * Tickets the agent coded with a real code are NEVER overridden.

Known blind spot: the model has never seen a true 'goodwill' example (GW-OTHER is the only goodwill
code, so it has no clean training labels). Genuine goodwill is therefore pushed to another code
unless the model is unsure. See README 'What is wrong with this'.
"""
import numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline, make_union

THRESHOLD = 0.60
C = 1.0
DEFAULT_CODE = "GW-OTHER"

def build_text(df):
    t = (df.agent_notes.fillna("") + " || " + df.customer_message.fillna("")).str.lower().str.replace("\\n", " ", regex=False)
    bucket = pd.cut(df.days_since_order, [-99999, 7, 14, 30, 90, 99999], labels=False).astype(str)
    return t + " dso_" + bucket

def make_model():
    feats = make_union(TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True),
                       TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True))
    return make_pipeline(feats, LogisticRegression(C=C, max_iter=2000))

def recode(refunds):
    """refunds: DataFrame of refund tickets (is_refund == True). Returns copy with model_code, model_conf, final_code."""
    r = refunds.copy()
    r["text"] = build_text(r)
    labelled = r.refund_reason_code != DEFAULT_CODE
    model = make_model().fit(r.loc[labelled, "text"], r.loc[labelled, "refund_reason_code"])
    proba = model.predict_proba(r["text"])
    r["model_code"] = model.classes_[proba.argmax(1)]
    r["model_conf"] = proba.max(1)
    take = (~labelled) & (r.model_conf >= THRESHOLD)
    r["final_code"] = np.where(take, r.model_code, r.refund_reason_code)
    r["recoded"] = take
    return r.drop(columns="text")
