"""Shared helpers: find input files by suffix (the pack's filenames carry random prefixes)."""
import glob, os
import pandas as pd

def find(data_dir, name):
    hits = glob.glob(os.path.join(data_dir, f"*{name}"))
    if not hits:
        raise FileNotFoundError(f"No file ending in '{name}' under {data_dir}")
    return hits[0]

def load(data_dir, name, **kw):
    return pd.read_csv(find(data_dir, name), **kw)
