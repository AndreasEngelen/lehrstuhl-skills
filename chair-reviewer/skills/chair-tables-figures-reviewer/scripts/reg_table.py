#!/usr/bin/env python3
"""Build a Chair-style regression table (Word) from a JSON specification.

Usage
-----
python reg_table.py spec.json Table_Regression.docx

The spec separates content from layout. Minimal example (see
references/reg_table_example.json for a full one):

{
  "number": "3",
  "title": "Zero-inflated negative binomial regression of co-founder turnover",
  "dv_spanners": [{"label": "Co-founder turnover", "span": [1, 3]}],
  "models": [{"name": "Model 1", "label": "Controls only"},
             {"name": "Model 2", "label": "Direct effects", "hypotheses": "H1, H2"},
             {"name": "Model 3", "label": "Full model", "hypotheses": "H3"}],
  "blocks": [
    {"label": "Independent variables",
     "rows": [{"label": "Mean narcissism", "cells": [null, {"b": 0.35, "se": 0.08, "p": 0.0002}, ...]}]},
    {"label": "Control variables", "rows": [...]}
  ],
  "indicator_rows": [{"label": "Year fixed effects", "cells": ["Included", "Included", "Included"]}],
  "stat_rows": [{"label": "Observations", "cells": [83577, 83577, 83577], "decimals": 0},
                {"label": "Ventures", "cells": [911, 911, 911], "decimals": 0},
                {"label": "Wald χ²", "cells": [{"b": 312.4, "p": 0.0001}, ...], "decimals": 2}],
  "decimals": 3,
  "se_position": "below",            # "below" (default) or "inline"
  "parentheses": "se",               # "se", "ci", "p", or "t"
  "stars": "chair",                  # "chair" (+ .10, * .05, ** .01, *** .001), "econ", or "none"
  "two_tailed": true,
  "se_text": "Robust standard errors clustered at the venture level",
  "estimator": "Zero-inflated negative binomial regression",
  "note": "Additional note text (abbreviations, transformations)."
}

A cell may also be given as {"b": .., "lo": .., "hi": ..} when parentheses = "ci".
Rows with no estimate for a model use null (printed as blank). Every blank must
be explained in the note if it is not self-evident.

The script warns when a coefficient would print as 0.000 at the chosen
precision (rescale the variable), when p-values and stars would disagree, and
when a model lacks N or fit statistics.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _docx_common import (add_caption, add_note, fmt_num, new_document,  # noqa: E402
                          new_table, rule_above, rule_below, set_cell, usable_width_cm)

STAR_SETS = {
    "chair": [(0.001, "***"), (0.01, "**"), (0.05, "*"), (0.10, "+")],
    "econ": [(0.01, "***"), (0.05, "**"), (0.10, "*")],
    "none": [],
}
LEGEND = {
    "chair": "+p < .10. *p < .05. **p < .01. ***p < .001",
    "econ": "*p < .10. **p < .05. ***p < .01",
}


def star(p, scheme):
    if p is None:
        return ""
    for thr, s in STAR_SETS[scheme]:
        if p < thr:
            return s
    return ""


def main():
    spec_path, out = sys.argv[1], sys.argv[2]
    s = json.load(open(spec_path, encoding="utf-8"))
    models = s["models"]
    m = len(models)
    dec = s.get("decimals", 3)
    lz = s.get("leading_zero", True)
    below = s.get("se_position", "below") == "below"
    par = s.get("parentheses", "se")
    scheme = s.get("stars", "chair")
    warn = []

    # build the grid as a list of rows: (kind, label, cells)
    grid = []
    for blk in s["blocks"]:
        if blk.get("label"):
            grid.append(("block", blk["label"], [""] * m))
        for row in blk["rows"]:
            main_cells, sub_cells = [], []
            for j, c in enumerate(row["cells"]):
                if c is None:
                    main_cells.append(("", None))
                    sub_cells.append("")
                    continue
                b = c.get("b")
                if b is not None and b != 0 and abs(b) < 0.5 * 10 ** (-dec):
                    warn.append(f"'{row['label']}' in {models[j]['name']} prints as 0 at {dec} decimals: "
                                "rescale the variable (e.g., thousands/millions) or report more decimals")
                st = star(c.get("p"), scheme)
                btxt = fmt_num(b, dec, lz)
                if par == "se":
                    ptxt = f"({fmt_num(c.get('se'), dec, lz)})" if c.get("se") is not None else ""
                elif par == "ci":
                    ptxt = f"[{fmt_num(c['lo'], dec, lz)}, {fmt_num(c['hi'], dec, lz)}]" if "lo" in c else ""
                elif par == "t":
                    ptxt = f"({fmt_num(c.get('t'), 2, lz)})" if c.get("t") is not None else ""
                else:  # exact p
                    pv = c.get("p")
                    ptxt = "" if pv is None else ("(< .001)" if pv < .001 else f"({fmt_num(pv, 3, False)})")
                if c.get("se") and c.get("p") is not None and b:
                    z = abs(b / c["se"])
                    import math
                    from scipy import stats
                    p_approx = 2 * (1 - stats.norm.cdf(z))
                    if star(p_approx, scheme) != st and abs(p_approx - c["p"]) > 0.02:
                        warn.append(f"'{row['label']}' {models[j]['name']}: p = {c['p']} but b/SE implies p ≈ {p_approx:.3f}; "
                                    "check stars (fine for t with few df or non-normal tests)")
                if below:
                    main_cells.append((btxt, st))
                    sub_cells.append(ptxt)
                else:
                    main_cells.append((f"{btxt} {ptxt}".strip(), st))
            grid.append(("coef", row["label"], main_cells))
            if below:
                grid.append(("se", "", sub_cells))
    for r in s.get("indicator_rows", []):
        grid.append(("ind", r["label"], r["cells"]))
    stat_rows = s.get("stat_rows", [])
    labels_lower = [r["label"].lower() for r in stat_rows]
    if not any(k in " ".join(labels_lower) for k in ("observations", "n")):
        warn.append("No 'Observations' row: report N for every model (and the number of firms/ventures for panels)")
    if not any(k in " ".join(labels_lower) for k in ("r²", "r2", "log", "χ²", "chi", "aic", "wald", "f")):
        warn.append("No fit statistic: add the statistic that fits the estimator (R², pseudo R², log-likelihood, Wald χ², AIC)")
    for r in stat_rows:
        cells = []
        for c in r["cells"]:
            if isinstance(c, dict):
                cells.append((fmt_num(c.get("b"), r.get("decimals", 2), lz), star(c.get("p"), scheme)))
            elif c is None:
                cells.append(("", None))
            else:
                cells.append((fmt_num(c, r.get("decimals", 2), lz) if not isinstance(c, str) else c, None))
        grid.append(("stat", r["label"], cells))

    # header rows
    header = []
    if s.get("dv_spanners"):
        header.append("dv")
    header.append("model")
    if any(mm.get("label") for mm in models):
        header.append("mlabel")
    if any(mm.get("hypotheses") for mm in models):
        header.append("hyp")

    doc = new_document(landscape=(m > 6))
    add_caption(doc, s.get("number", "1"), s["title"])
    uw = usable_width_cm(doc)
    first = min(7.0, max(4.5, uw * 0.38))
    t = new_table(doc, rows=len(header) + len(grid), cols=m + 1, first_col_cm=first, other_col_cm=(uw - first) / m)
    size = 9 if m <= 6 else 8
    hr = 0
    for h in header:
        if h == "dv":
            set_cell(t.cell(hr, 0), "Dependent variable", italic=True, align="left", size=size)
            for sp in s["dv_spanners"]:
                a, b = sp["span"]
                cell = t.cell(hr, a).merge(t.cell(hr, b)) if b > a else t.cell(hr, a)
                set_cell(cell, sp["label"], size=size)
        elif h == "model":
            for j, mm in enumerate(models, start=1):
                set_cell(t.cell(hr, j), mm["name"], size=size)
        elif h == "mlabel":
            for j, mm in enumerate(models, start=1):
                set_cell(t.cell(hr, j), mm.get("label", ""), italic=True, size=size - 1)
        elif h == "hyp":
            set_cell(t.cell(hr, 0), "Hypotheses tested", italic=True, align="left", size=size - 1)
            for j, mm in enumerate(models, start=1):
                set_cell(t.cell(hr, j), mm.get("hypotheses", ""), size=size - 1)
        hr += 1
    first_stat = None
    for i, (kind, label, cells) in enumerate(grid):
        row = hr + i
        if kind == "block":
            set_cell(t.cell(row, 0), label, italic=True, align="left", size=size)
            continue
        indent = "    " if kind == "coef" else ""
        set_cell(t.cell(row, 0), indent + label if kind == "coef" else label, align="left", size=size)
        for j, c in enumerate(cells, start=1):
            if isinstance(c, tuple):
                set_cell(t.cell(row, j), c[0], size=size, superscript=c[1] or None)
            else:
                set_cell(t.cell(row, j), c, size=size)
        if kind in ("ind", "stat") and first_stat is None:
            first_stat = row
    rule_above(t.rows[0], 12)
    rule_below(t.rows[hr - 1], 6)
    if first_stat is not None:
        rule_above(t.rows[first_stat], 4)
    rule_below(t.rows[-1], 12)

    # note
    parts = []
    if s.get("estimator"):
        parts.append(s["estimator"].rstrip(".") + ".")
    what = {"se": s.get("se_text", "Standard errors") + " in parentheses.",
            "ci": "95% confidence intervals in brackets.",
            "p": "Exact p-values in parentheses.",
            "t": "t-statistics in parentheses."}[par]
    parts.append(what)
    if s.get("note"):
        parts.append(s["note"].strip())
    if scheme != "none":
        parts.append(LEGEND[scheme] + (" (two-tailed)." if s.get("two_tailed", True) else " (one-tailed)."))
    add_note(doc, " ".join(parts))
    doc.save(out)
    print(f"Wrote {out}")
    if warn:
        print("\nChecks:")
        for w in dict.fromkeys(warn):
            print(" -", w)


if __name__ == "__main__":
    main()
