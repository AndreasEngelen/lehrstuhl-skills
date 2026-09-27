#!/usr/bin/env python3
"""Chair-style interaction plots: simple slopes, Johnson–Neyman, or plotted predictions.

Three modes (all write PNG at 600 dpi plus vector PDF and SVG):

1) slopes  – from regression coefficients (linear predictor):
   python interaction_plot.py slopes spec.json out_basename
   spec = {
     "x_label": "Mean narcissism (standardized)", "y_label": "Predicted co-founder turnover",
     "m_label": "Narcissism diversity",
     "b": {"const": 0.10, "x": 0.35, "m": -0.12, "xm": -0.18},   # add "controls_at_mean": value if needed
     "vcov": [[...4x4 in order const, x, m, xm...]],               # optional -> CI bands and slope tests
     "x_mean": 0, "x_sd": 1, "m_mean": 0, "m_sd": 1,
     "m_levels": "sd" | [values],  "m_level_labels": ["Low (−1 SD)", "High (+1 SD)"],
     "x_range": [-1, 1] (default mean ± 1 SD),
     "link": "identity" | "exp" | "logit",   # transform the linear predictor for count/logit models
     "df_resid": 200                          # optional, t instead of z for slope tests
   }
   Also writes <out>_simple_slopes.csv (slope, SE, z/t, p at each moderator level) –
   report these in a small table or in the figure note.

2) jn – Johnson–Neyman plot of the conditional effect of x across the moderator:
   python interaction_plot.py jn spec.json out_basename
   uses the same spec ("b", "vcov" required), plus "m_range": [min, max] and optionally
   "m_values_file": CSV with one column of observed moderator values -> share of
   observations in the region of significance is computed and printed.

3) points – from predictions you computed elsewhere (e.g., Stata margins, R ggeffects):
   python interaction_plot.py points preds.csv out_basename --x x --y yhat --group level \
          [--lo lo --hi hi] [--x-label ..] [--y-label ..] [--m-label ..]

Design defaults: black-and-white, distinct line styles plus direct labels, CI bands
when available, axis titles with units, same y-scale across panels, no chart junk.
"""
import argparse
import csv
import json
import math
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy import stats  # noqa: E402

STYLES = [("-", "black"), ("--", "black"), (":", "black"), ("-.", "dimgray"), ((0, (5, 1, 1, 1)), "dimgray")]


def setup():
    plt.rcParams.update({
        "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.8, "legend.frameon": False, "savefig.bbox": "tight",
    })


def save(fig, base):
    for ext, kw in (("png", {"dpi": 600}), ("pdf", {}), ("svg", {})):
        fig.savefig(f"{base}.{ext}", **kw)
    print(f"Wrote {base}.png/.pdf/.svg")


def inv_link(eta, link):
    if link == "exp":
        return np.exp(eta)
    if link == "logit":
        return 1 / (1 + np.exp(-eta))
    return eta


def slopes(spec, base):
    b = spec["b"]
    V = np.array(spec["vcov"]) if spec.get("vcov") else None
    xm, xs = spec.get("x_mean", 0), spec.get("x_sd", 1)
    mm, ms = spec.get("m_mean", 0), spec.get("m_sd", 1)
    lv = spec.get("m_levels", "sd")
    levels = [mm - ms, mm + ms] if lv == "sd" else lv
    names = spec.get("m_level_labels") or (["Low (−1 SD)", "High (+1 SD)"] if lv == "sd" else [f"{v:g}" for v in levels])
    xr = spec.get("x_range", [xm - xs, xm + xs])
    xg = np.linspace(xr[0], xr[1], 50)
    link = spec.get("link", "identity")
    c0 = b.get("controls_at_mean", 0)
    fig, ax = plt.subplots(figsize=(4.2, 3.2))
    rows = []
    df = spec.get("df_resid")
    for k, (m, name) in enumerate(zip(levels, names)):
        eta = c0 + b["const"] + b["x"] * xg + b["m"] * m + b["xm"] * xg * m
        ls, col = STYLES[k % len(STYLES)]
        ax.plot(xg, inv_link(eta, link), linestyle=ls, color=col, lw=1.4)
        if V is not None:
            A = np.column_stack([np.ones_like(xg), xg, np.full_like(xg, m), xg * m])
            se = np.sqrt(np.einsum("ij,jk,ik->i", A, V, A))
            ax.fill_between(xg, inv_link(eta - 1.96 * se, link), inv_link(eta + 1.96 * se, link),
                            color="0.85", alpha=0.6, lw=0)
            sl = b["x"] + b["xm"] * m
            sse = math.sqrt(V[1, 1] + m * m * V[3, 3] + 2 * m * V[1, 3])
            stat = sl / sse
            p = 2 * (1 - (stats.t.cdf(abs(stat), df) if df else stats.norm.cdf(abs(stat))))
            rows.append({"moderator_level": name, "value": float(m), "slope": float(sl), "se": float(sse),
                         ("t" if df else "z"): float(stat), "p": float(p)})
        ax.annotate(name, xy=(xg[-1], inv_link(eta[-1], link)), xytext=(4, 0),
                    textcoords="offset points", va="center", fontsize=8.5)
    ax.set_xlabel(spec.get("x_label", "X"))
    ax.set_ylabel(spec.get("y_label", "Predicted Y"))
    if spec.get("m_label"):
        ax.set_title(spec["m_label"], fontsize=9, loc="left", style="italic")
    save(fig, base)
    if rows:
        with open(f"{base}_simple_slopes.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        for r in rows:
            print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})


def jn(spec, base):
    b, V = spec["b"], np.array(spec["vcov"])
    lo, hi = spec["m_range"]
    mg = np.linspace(lo, hi, 400)
    sl = b["x"] + b["xm"] * mg
    se = np.sqrt(V[1, 1] + mg ** 2 * V[3, 3] + 2 * mg * V[1, 3])
    crit = stats.t.ppf(.975, spec["df_resid"]) if spec.get("df_resid") else 1.96
    sig = np.abs(sl / se) > crit
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    ax.fill_between(mg, sl - crit * se, sl + crit * se, color="0.85", lw=0, label="95% CI")
    ax.plot(mg, sl, color="black", lw=1.4, label="Conditional effect")
    ax.axhline(0, color="black", lw=0.6)
    changes = np.where(np.diff(sig.astype(int)) != 0)[0]
    bounds = [float((mg[i] + mg[i + 1]) / 2) for i in changes]
    for bd in bounds:
        ax.axvline(bd, color="black", ls=":", lw=0.9)
    ax.set_xlabel(spec.get("m_label", "Moderator"))
    ax.set_ylabel(f"Effect of {spec.get('x_label', 'X')}")
    ax.legend(loc="best", fontsize=8)
    save(fig, base)
    print("Johnson–Neyman boundaries:", [round(x, 4) for x in bounds] or "none in range")
    if spec.get("m_values_file"):
        vals = np.loadtxt(spec["m_values_file"], delimiter=",", skiprows=1)
        s_obs = np.abs((b["x"] + b["xm"] * vals) /
                       np.sqrt(V[1, 1] + vals ** 2 * V[3, 3] + 2 * vals * V[1, 3])) > crit
        print(f"Share of observations in the region of significance: {s_obs.mean():.1%} – report it in the caption or text")


def points(a, base):
    rows = list(csv.DictReader(open(a.data)))
    groups = list(dict.fromkeys(r[a.group] for r in rows))
    fig, ax = plt.subplots(figsize=(4.2, 3.2))
    for k, g in enumerate(groups):
        rr = sorted([r for r in rows if r[a.group] == g], key=lambda r: float(r[a.x]))
        x = np.array([float(r[a.x]) for r in rr])
        y = np.array([float(r[a.y]) for r in rr])
        ls, col = STYLES[k % len(STYLES)]
        if a.lo and a.hi:
            ax.fill_between(x, [float(r[a.lo]) for r in rr], [float(r[a.hi]) for r in rr], color="0.85", alpha=0.6, lw=0)
        ax.plot(x, y, linestyle=ls, color=col, lw=1.4, marker="o" if len(x) <= 5 else None, ms=3)
        ax.annotate(g, xy=(x[-1], y[-1]), xytext=(4, 0), textcoords="offset points", va="center", fontsize=8.5)
    ax.set_xlabel(a.x_label or a.x)
    ax.set_ylabel(a.y_label or a.y)
    if a.m_label:
        ax.set_title(a.m_label, fontsize=9, loc="left", style="italic")
    save(fig, base)


if __name__ == "__main__":
    setup()
    mode = sys.argv[1]
    if mode in ("slopes", "jn"):
        spec = json.load(open(sys.argv[2], encoding="utf-8"))
        (slopes if mode == "slopes" else jn)(spec, sys.argv[3])
    elif mode == "points":
        ap = argparse.ArgumentParser()
        ap.add_argument("mode")
        ap.add_argument("data")
        ap.add_argument("out")
        for opt in ("--x", "--y", "--group", "--lo", "--hi", "--x-label", "--y-label", "--m-label"):
            ap.add_argument(opt)
        a = ap.parse_args()
        points(a, a.out)
    else:
        raise SystemExit("mode must be slopes, jn or points")
