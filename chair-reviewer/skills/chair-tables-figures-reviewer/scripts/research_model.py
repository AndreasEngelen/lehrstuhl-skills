#!/usr/bin/env python3
"""Draw a Chair-style research-model figure (boxes and arrows) from a JSON spec.

Usage:  python research_model.py model.json out_basename
Writes out_basename.png (600 dpi), .pdf and .svg (vector; the SVG/PDF can be
edited in PowerPoint, Illustrator or Inkscape).

Spec example:
{
  "constructs": [
    {"id": "fe",  "label": "Founding experience", "role": "iv", "measures": ["Number of previous ventures"]},
    {"id": "ac",  "label": "Absorptive capacity", "role": "mediator"},
    {"id": "io",  "label": "Innovation output", "role": "dv", "measures": ["Patent applications"]},
    {"id": "vc",  "label": "Prior VC investor exposure", "role": "moderator"}
  ],
  "paths": [
    {"from": "fe", "to": "ac", "label": "H1 (+)"},
    {"from": "ac", "to": "io", "label": "H3 (+)"},
    {"from": "vc", "on": ["fe", "ac"], "label": "H2 (+)"},
    {"from": "fe", "to": "io", "label": "", "style": "dashed"}
  ],
  "note_labels": ["H4: indirect effect via absorptive capacity"],
  "controls": {"Venture level": ["Venture age", "Team size"], "Industry level": ["Industry dummies"]}
}

Roles: iv (left column), mediator (middle), dv (right), moderator (above the path
it moderates; its arrow points onto that path). "on" = [from, to] of the moderated
path. Path styles: "solid" (default) or "dashed" (e.g., non-hypothesized paths).
Every hypothesized arrow should carry its H label and expected sign.
"""
import json
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402

K = 0.40            # inches per data unit
CH = 0.078 / K      # approx. width of one character at 10 pt (data units)
LINE = 0.17 / K     # line height at 10 pt
WRAP = 22
W = WRAP * CH * 0.95 + 0.6
PAD = 0.55
GAP_COL = 4.2       # horizontal gap between box edges
GAP_ROW = 0.9


def wrap(s, n=WRAP):
    return textwrap.wrap(s, n) or [""]


def lines_of(c):
    return [(t, "b") for t in wrap(c["label"])] + [(t, "i") for m in c.get("measures", []) for t in wrap(m, WRAP + 4)]


def main():
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    base = sys.argv[2]
    C = {c["id"]: dict(c) for c in spec["constructs"]}
    for c in C.values():
        c["lines"] = lines_of(c)
        c["h"] = len(c["lines"]) * LINE + PAD
    roles = {r: [c["id"] for c in spec["constructs"] if c["role"] == r] for r in ("iv", "mediator", "dv", "moderator")}
    cols = ["iv", "mediator", "dv"] if roles["mediator"] else ["iv", "dv"]
    for i, role in enumerate(cols):
        ids = roles[role]
        total = sum(C[i_]["h"] for i_ in ids) + GAP_ROW * (len(ids) - 1)
        y = total / 2
        for i_ in ids:
            C[i_]["x"] = i * (W + GAP_COL)
            C[i_]["y"] = y - C[i_]["h"] / 2
            y -= C[i_]["h"] + GAP_ROW

    def edge(a, b):
        return (a["x"] + W / 2, a["y"]), (b["x"] - W / 2, b["y"])

    paths = spec.get("paths", [])
    core_ids = [i for r in cols for i in roles[r]]
    top = max(C[i]["y"] + C[i]["h"] / 2 for i in core_ids)
    bottom = min(C[i]["y"] - C[i]["h"] / 2 for i in core_ids)
    mids, draws = {}, []
    for p in paths:
        if "to" not in p:
            continue
        a, b = C[p["from"]], C[p["to"]]
        ls = p.get("style", "solid")
        if a["role"] == "iv" and b["role"] == "dv" and roles["mediator"]:
            bottom -= 1.0
            yb = bottom
            draws.append(("poly", [(a["x"], a["y"] - a["h"] / 2), (a["x"], yb), (b["x"], yb), (b["x"], b["y"] - b["h"] / 2)], ls))
            mids[(p["from"], p["to"])] = ((a["x"] + b["x"]) / 2, yb)
            if p.get("label"):
                draws.append(("text", ((a["x"] + b["x"]) / 2, yb - 0.25), p["label"], "top"))
        else:
            (x1, y1), (x2, y2) = edge(a, b)
            draws.append(("arrow", (x1, y1), (x2, y2), ls))
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            mids[(p["from"], p["to"])] = (mx, my)
            moderated = any(q.get("on") == [p["from"], p["to"]] for q in paths)
            if p.get("label"):
                f = 0.28 if moderated else 0.5   # keep the label clear of a moderator arrow
                draws.append(("text", (x1 + f * (x2 - x1), y1 + f * (y2 - y1) + 0.22), p["label"], "bottom"))
    used = {}
    mod_top = top
    for p in paths:
        if "on" not in p:
            continue
        key = tuple(p["on"])
        mx, my = mids[key]
        k = used.get(key, 0)
        used[key] = k + 1
        m = C[p["from"]]
        if "x" not in m:
            m["x"] = mx + k * (W + 0.8)
            m["y"] = top + 1.8 + m["h"] / 2
            mod_top = max(mod_top, m["y"] + m["h"] / 2)
        tx = mx + k * 0.5
        draws.append(("arrow", (m["x"], m["y"] - m["h"] / 2), (tx, my + 0.08), p.get("style", "solid")))
        if p.get("label"):
            draws.append(("text_l", (tx + 0.2, (m["y"] - m["h"] / 2 + my) / 2 + 0.3), p["label"]))
    # controls
    ctrl = None
    if spec.get("controls"):
        txt = [("Controls", "b")] + [(t, "n") for g, items in spec["controls"].items()
                                     for t in wrap(f"{g}: " + ", ".join(items), 60)]
        h = len(txt) * LINE * 0.9 + 0.5
        dv = C[roles["dv"][-1]]
        cw = 60 * CH * 0.85 + 0.6
        cx = dv["x"] + W / 2 - cw / 2 - 1.2
        cy = bottom - 1.0 - h / 2
        ctrl = (cx, cy, cw, h, txt)
        draws.append(("carrow", (cx + cw / 2, cy + h / 2), (dv["x"] + W / 2 - 0.4, dv["y"] - dv["h"] / 2)))
        bottom = cy - h / 2
    notes = spec.get("note_labels", [])
    xmin = min(c["x"] for c in C.values() if "x" in c) - W / 2
    xmax = max(c["x"] for c in C.values() if "x" in c) + W / 2
    if ctrl:
        xmin = min(xmin, ctrl[0] - ctrl[2] / 2)
    ymin = bottom - 0.4 - len(notes) * LINE
    ymax = mod_top + 0.4
    fig = plt.figure(figsize=((xmax - xmin + 1.0) * K, (ymax - ymin + 0.6) * K))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(xmin - 0.5, xmax + 0.5)
    ax.set_ylim(ymin - 0.3, ymax + 0.3)
    ax.axis("off")
    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"]})

    def box(c):
        ax.add_patch(Rectangle((c["x"] - W / 2, c["y"] - c["h"] / 2), W, c["h"], fc="white", ec="black", lw=1.0, zorder=2))
        n = len(c["lines"])
        for i, (t, st) in enumerate(c["lines"]):
            ax.text(c["x"], c["y"] + (n - 1) * LINE / 2 - i * LINE, t, ha="center", va="center", zorder=3,
                    fontsize=10 if st == "b" else 8.5, fontweight="bold" if st == "b" else "normal",
                    style="italic" if st == "i" else "normal")

    for d in draws:
        if d[0] == "arrow":
            ax.add_patch(FancyArrowPatch(d[1], d[2], arrowstyle="-|>", mutation_scale=11, lw=1.0, color="black",
                                         linestyle=d[3], zorder=1, shrinkA=0, shrinkB=0))
        elif d[0] == "poly":
            pts = d[1]
            xs, ys = zip(*pts[:-1])
            ax.plot(list(xs) + [pts[-1][0]], list(ys) + [pts[-2][1]], color="black", lw=1.0, ls=d[2], zorder=1)
            ax.add_patch(FancyArrowPatch(pts[-2], pts[-1], arrowstyle="-|>", mutation_scale=11, lw=1.0,
                                         color="black", linestyle=d[2], shrinkA=0, shrinkB=0))
        elif d[0] == "carrow":
            ax.add_patch(FancyArrowPatch(d[1], d[2], arrowstyle="-|>", mutation_scale=9, lw=0.8, color="black",
                                         linestyle=":", connectionstyle="arc3,rad=0.2", shrinkA=0, shrinkB=0))
        elif d[0] == "text":
            ax.text(*d[1], d[2], ha="center", va=d[3], fontsize=9.5, zorder=4,
                    bbox=dict(fc="white", ec="none", pad=0.3))
        elif d[0] == "text_l":
            ax.text(*d[1], d[2], ha="left", va="center", fontsize=9.5, zorder=4)
    for c in C.values():
        if "x" in c:
            box(c)
    if ctrl:
        cx, cy, cw, h, txt = ctrl
        ax.add_patch(Rectangle((cx - cw / 2, cy - h / 2), cw, h, fc="white", ec="black", lw=0.8, ls="--"))
        for i, (t, st) in enumerate(txt):
            ax.text(cx - cw / 2 + 0.3, cy + h / 2 - 0.45 - i * LINE * 0.9, t, ha="left", va="center",
                    fontsize=8.5, fontweight="bold" if st == "b" else "normal")
    for i, t in enumerate(notes):
        ax.text(xmin, bottom - 0.4 - i * LINE, t, ha="left", va="top", fontsize=8.5, style="italic")
    for ext, kw in (("png", {"dpi": 600}), ("pdf", {}), ("svg", {})):
        fig.savefig(f"{base}.{ext}", **kw)
    print(f"Wrote {base}.png/.pdf/.svg")


if __name__ == "__main__":
    main()
