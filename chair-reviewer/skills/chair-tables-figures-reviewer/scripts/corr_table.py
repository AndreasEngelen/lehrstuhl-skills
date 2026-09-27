#!/usr/bin/env python3
"""Build a Chair-style descriptives-and-correlations table (Word) from raw data.

Usage
-----
python corr_table.py --data data.csv --out Table_Correlations.docx \
    [--vars dv iv1 iv2 ...] [--labels labels.json] [--decimals 2] \
    [--sig rule|stars|none] [--no-minmax] [--pairwise] \
    [--number 2] [--title "Means, standard deviations, and correlations"] \
    [--unit "firm-year observations"] [--clusters 708 --cluster-unit firms] \
    [--note-extra "Variables are shown before log transformation."]

Data may be .csv, .xlsx, .dta, .sav or .parquet. The order of --vars is the
order of the table (Chair convention: DV(s), IV(s), moderators/mediators,
controls). labels.json maps variable names to reader-friendly labels
(no software codes).

Prints plausibility warnings (dummy SDs, constant variables, very skewed
variables, |r| > .70) to stdout and writes the same numbers to a CSV next to
the Word file so they can be checked.
"""
import argparse
import json
import math
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _docx_common import (add_caption, add_note, fmt_num, new_document,  # noqa: E402
                          new_table, rule_above, rule_below, set_cell, usable_width_cm)


def load(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        return pd.read_csv(path)
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(path)
    if ext == ".dta":
        return pd.read_stata(path)
    if ext == ".sav":
        return pd.read_spss(path)
    if ext == ".parquet":
        return pd.read_parquet(path)
    raise SystemExit(f"Unsupported file type: {ext}")


def critical_r(n, alpha=0.05):
    """Smallest |r| that is significant (two-tailed) for sample size n."""
    if n <= 3:
        return float("nan")
    t = stats.t.ppf(1 - alpha / 2, n - 2)
    return t / math.sqrt(t * t + n - 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--vars", nargs="*")
    ap.add_argument("--labels")
    ap.add_argument("--decimals", type=int, default=2)
    ap.add_argument("--sig", choices=["rule", "stars", "none"], default="rule")
    ap.add_argument("--no-minmax", action="store_true")
    ap.add_argument("--pairwise", action="store_true", help="pairwise instead of listwise deletion")
    ap.add_argument("--number", default="1")
    ap.add_argument("--title", default="Means, standard deviations, minima, maxima, and correlations")
    ap.add_argument("--unit", default="observations")
    ap.add_argument("--clusters", type=int)
    ap.add_argument("--cluster-unit", default="firms")
    ap.add_argument("--note-extra", default="")
    ap.add_argument("--no-leading-zero", action="store_true")
    a = ap.parse_args()

    df = load(a.data)
    vars_ = a.vars or [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    missing = [v for v in vars_ if v not in df.columns]
    if missing:
        raise SystemExit(f"Variables not in data: {missing}")
    labels = json.load(open(a.labels)) if a.labels else {}
    d = df[vars_].apply(pd.to_numeric, errors="coerce")
    if not a.pairwise:
        d = d.dropna()
    n = len(d) if not a.pairwise else int(d.notna().all(axis=1).sum())
    k = len(vars_)
    lz = not a.no_leading_zero
    dec = a.decimals

    # statistics
    desc = pd.DataFrame({"mean": d.mean(), "sd": d.std(ddof=1), "min": d.min(), "max": d.max()})
    r = np.full((k, k), np.nan)
    p = np.full((k, k), np.nan)
    npair = np.zeros((k, k), dtype=int)
    for i in range(k):
        for j in range(i):
            x, y = d.iloc[:, i], d.iloc[:, j]
            m = x.notna() & y.notna()
            npair[i, j] = int(m.sum())
            if m.sum() > 3 and x[m].std() > 0 and y[m].std() > 0:
                r[i, j], p[i, j] = stats.pearsonr(x[m], y[m])

    # plausibility warnings
    warn = []
    for v in vars_:
        col = d[v].dropna()
        vals = set(col.unique())
        if col.std() == 0:
            warn.append(f"{v}: constant variable (SD = 0)")
        if vals <= {0, 1} and len(vals) == 2 and "=" not in labels.get(v, v):
            warn.append(f"{v}: dummy variable; state the coding in the label, e.g. '(1 = yes)'")
        if col.min() >= 0 and col.std() > 0 and col.skew() > 3:
            warn.append(f"{v}: strongly right-skewed (skew {col.skew():.1f}); models often use a log; "
                        "state in the table whether values are shown before or after transformation")
        if col.abs().max() >= 10 ** 4:
            warn.append(f"{v}: large values (max {col.max():,.0f}); consider rescaling (e.g., in thousands) "
                        "so regression coefficients do not print as 0.00")
    for i in range(k):
        for j in range(i):
            if not np.isnan(r[i, j]) and abs(r[i, j]) > 0.70:
                warn.append(f"|r| = {abs(r[i,j]):.2f} between {vars_[i]} and {vars_[j]}: check multicollinearity, "
                            "report VIFs in the text or note")

    # write CSV for checking
    base = os.path.splitext(a.out)[0]
    out_csv = base + "_values.csv"
    tab = desc.copy()
    for j in range(k - 1):
        tab[str(j + 1)] = [r[i, j] if i > j else np.nan for i in range(k)]
    tab.to_csv(out_csv)

    # Word table
    show_minmax = not a.no_minmax
    stat_cols = ["M", "SD"] + (["Min", "Max"] if show_minmax else [])
    ncols = 1 + len(stat_cols) + (k - 1)
    doc = new_document(landscape=(ncols > 10))
    add_caption(doc, a.number, a.title)
    size = 9 if k <= 12 else 8 if k <= 18 else 7
    uw = usable_width_cm(doc)
    first = min(5.0, max(3.0, 0.17 * size / 9 * max(len(labels.get(v, v)) for v in vars_) + 0.6))
    t = new_table(doc, rows=k + 1, cols=ncols, first_col_cm=first, other_col_cm=(uw - first) / (ncols - 1))
    set_cell(t.cell(0, 0), "Variable", align="left", size=size)
    for c, h in enumerate(stat_cols, start=1):
        set_cell(t.cell(0, c), h, italic=True, size=size)
    for j in range(k - 1):
        set_cell(t.cell(0, 1 + len(stat_cols) + j), str(j + 1), size=size)
    rcrit = critical_r(n)
    for i, v in enumerate(vars_):
        row = i + 1
        set_cell(t.cell(row, 0), f"{i+1}. {labels.get(v, v)}", align="left", size=size)
        vals = [desc.loc[v, "mean"], desc.loc[v, "sd"]] + ([desc.loc[v, "min"], desc.loc[v, "max"]] if show_minmax else [])
        for c, x in enumerate(vals, start=1):
            set_cell(t.cell(row, c), fmt_num(float(x), dec, lz), size=size)
        for j in range(i):
            txt = fmt_num(float(r[i, j]), dec, lz) if not np.isnan(r[i, j]) else "–"
            sup = None
            if a.sig == "stars" and not np.isnan(p[i, j]):
                sup = "***" if p[i, j] < .001 else "**" if p[i, j] < .01 else "*" if p[i, j] < .05 else None
            set_cell(t.cell(row, 1 + len(stat_cols) + j), txt, size=size, superscript=sup)
    rule_above(t.rows[0], 12)
    rule_below(t.rows[0], 6)
    rule_below(t.rows[-1], 12)

    note = f"N = {n:,} {a.unit}"
    if a.clusters:
        note += f" ({a.clusters:,} {a.cluster_unit})"
    note += "."
    if a.pairwise:
        note += " Correlations use pairwise deletion; Ns vary between " \
                f"{npair[np.tril_indices(k, -1)].min():,} and {npair[np.tril_indices(k, -1)].max():,}."
    if a.sig == "rule" and not math.isnan(rcrit):
        note += f" All correlations with |r| ≥ {fmt_num(math.ceil(rcrit * 10**dec) / 10**dec, dec, lz)} " \
                "are significant at p < .05 (two-tailed)."
        if n > 5000:
            note += " Given the large sample, magnitudes are more informative than significance."
    elif a.sig == "stars":
        note += " *p < .05. **p < .01. ***p < .001 (two-tailed)."
    if a.note_extra:
        note += " " + a.note_extra.strip()
    add_note(doc, note)
    doc.save(a.out)
    print(f"Wrote {a.out} and {out_csv}; N = {n}")
    if warn:
        print("\nPlausibility checks:")
        for w in warn:
            print(" -", w)


if __name__ == "__main__":
    main()
