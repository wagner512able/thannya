#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure 1 of the THANNYA manuscript: locus clustering and classification workflow.

Draws the three panels (A, B, C) plus the legend as a single vector figure,
sized for the full text width of BMC Bioinformatics (170 mm).

The figure is written as SVG using only the Python standard library, which is
the same output format THANNYA uses for its comparative maps.  The optional
PDF export uses cairosvg, already listed as an optional dependency of the
package.

Usage
-----
    python figures/fig1_workflow.py                 # writes fig1_workflow.svg
    python figures/fig1_workflow.py --pdf           # also writes .pdf
    python figures/fig1_workflow.py --png --dpi 600 # also writes a raster proof

All text, colours and geometry are defined in this file; edit the CONTENT
section near the bottom to change wording without touching the drawing code.
"""

from __future__ import annotations

import argparse
import os
from xml.sax.saxutils import escape

# --------------------------------------------------------------------------
# Page geometry.  One user unit = one typographic point, so font sizes in this
# file are the sizes the reader sees on the printed page.
# --------------------------------------------------------------------------

PT_PER_MM = 72.0 / 25.4
WIDTH_MM = 170.0                      # BMC full text width
WIDTH = WIDTH_MM * PT_PER_MM          # 481.89 pt

FONT = "Arial, Helvetica, sans-serif"

# Type scale (points at final size).  Nothing below 6 pt.
FS_PANEL = 10.5       # panel letter
FS_PANEL_TITLE = 9.5  # panel title
FS_TITLE = 7.6        # box title
FS_SUB = 6.4          # box subtitle
FS_DEC = 7.0          # decision title
FS_DEC_SUB = 6.3      # decision subtitle
FS_EDGE = 6.2         # Yes / No labels
FS_LOOP = 6.3         # dashed container captions
FS_LEGEND = 6.5

LH_TITLE = 8.6        # line height, title
LH_SUB = 7.2          # line height, subtitle

STROKE = 0.9          # default stroke width (well above the 0.25 pt minimum)
STROKE_THIN = 0.7

# --------------------------------------------------------------------------
# Palette.  Shape carries the meaning as well as colour (rounded = input or
# output, diamond = decision, rectangle = process), so the figure survives
# greyscale printing and colour-vision deficiency.
# --------------------------------------------------------------------------

STYLES = {
    "io":       {"fill": "#dbeafe", "stroke": "#2563eb", "text": "#1e3a8a"},
    "process":  {"fill": "#f8fafc", "stroke": "#334155", "text": "#0f172a"},
    "updated":  {"fill": "#dcfce7", "stroke": "#16a34a", "text": "#14532d"},
    "relaxed":  {"fill": "#ede9fe", "stroke": "#7c3aed", "text": "#4c1d95"},
    "discard":  {"fill": "#fee2e2", "stroke": "#dc2626", "text": "#7f1d1d"},
    "decision": {"fill": "#fef3c7", "stroke": "#d97706", "text": "#78350f"},
    "exclusive": {"fill": "#fde68a", "stroke": "#d97706", "text": "#78350f"},
    "thresh":   {"fill": "#f1f5f9", "stroke": "#0f172a", "text": "#0f172a"},
}

C_DARK = "#334155"
C_YES = "#16a34a"
C_NO = "#dc2626"
C_LOOP = "#94a3b8"
C_GOLD = "#f59e0b"


# --------------------------------------------------------------------------
# Minimal SVG writer
# --------------------------------------------------------------------------

class Canvas:
    def __init__(self, width: float):
        self.width = width
        self.body: list[str] = []
        self.height = 0.0

    def add(self, markup: str) -> None:
        self.body.append(markup)

    # -- primitives --------------------------------------------------------

    def text(self, x, y, s, size, *, weight="normal", fill="#0f172a",
             anchor="middle", style="normal"):
        self.add(
            f'<text x="{x:.2f}" y="{y:.2f}" font-family="{FONT}" '
            f'font-size="{size}" font-weight="{weight}" font-style="{style}" '
            f'fill="{fill}" text-anchor="{anchor}">{escape(s)}</text>'
        )

    def lines(self, cx, y, rows, size, lh, *, weight="normal", fill="#0f172a",
              style="normal"):
        """Draw stacked centred lines; y is the baseline of the first row."""
        for i, row in enumerate(rows):
            self.text(cx, y + i * lh, row, size, weight=weight, fill=fill,
                      style=style)

    def rect(self, x, y, w, h, *, fill, stroke, rx=2.0, sw=STROKE, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
            f'rx="{rx}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw}"{d}/>'
        )

    def diamond(self, cx, cy, w, h, *, fill, stroke, sw=STROKE):
        pts = (f"{cx:.2f},{cy - h / 2:.2f} {cx + w / 2:.2f},{cy:.2f} "
               f"{cx:.2f},{cy + h / 2:.2f} {cx - w / 2:.2f},{cy:.2f}")
        self.add(f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{sw}"/>')

    def circle(self, cx, cy, r, *, fill, stroke, sw=STROKE):
        self.add(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" '
                 f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def path(self, d, *, stroke=C_DARK, sw=STROKE, marker=True, dash=None,
             fill="none"):
        m = f' marker-end="url(#ah-{_key(stroke)})"' if marker else ""
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{sw}" stroke-linejoin="round" '
                 f'stroke-linecap="round"{da}{m}/>')

    def star(self, cx, cy, r, *, fill=C_GOLD, stroke="#b45309"):
        import math
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rad = r if i % 2 == 0 else r * 0.46
            pts.append(f"{cx + rad * math.cos(ang):.2f},"
                       f"{cy + rad * math.sin(ang):.2f}")
        self.add(f'<polygon points="{" ".join(pts)}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="0.6"/>')

    def cross(self, cx, cy, r, *, stroke="#0f172a"):
        self.add(
            f'<path d="M {cx - r:.2f} {cy - r:.2f} L {cx + r:.2f} {cy + r:.2f} '
            f'M {cx + r:.2f} {cy - r:.2f} L {cx - r:.2f} {cy + r:.2f}" '
            f'stroke="{stroke}" stroke-width="1.5" stroke-linecap="round"/>'
        )

    # -- document ----------------------------------------------------------

    def render(self) -> str:
        h_mm = self.height / PT_PER_MM
        defs = "".join(
            f'<marker id="ah-{_key(c)}" viewBox="0 0 10 10" refX="8.5" '
            f'refY="5" markerWidth="5.5" markerHeight="5.5" '
            f'markerUnits="strokeWidth" orient="auto">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{c}"/></marker>'
            for c in (C_DARK, C_YES, C_NO)
        )
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{WIDTH_MM:.2f}mm" height="{h_mm:.2f}mm" '
            f'viewBox="0 0 {self.width:.2f} {self.height:.2f}">\n'
            f'<defs>{defs}</defs>\n'
            f'<rect width="100%" height="100%" fill="#ffffff"/>\n'
            + "\n".join(self.body)
            + "\n</svg>\n"
        )


def _key(colour: str) -> str:
    return colour.lstrip("#")


# --------------------------------------------------------------------------
# Composite shapes.  Each returns the vertical extent it consumed so the
# callers can stack elements without hard-coding every coordinate.
# --------------------------------------------------------------------------

def box(c: Canvas, cx, y, w, title, subs, kind="process", rx=2.0):
    """Rectangular node.  Returns (y_top, y_bottom)."""
    st = STYLES[kind]
    pad = 4.8
    h = pad * 2 + LH_TITLE + (LH_SUB * len(subs) if subs else 0) - 1.6
    c.rect(cx - w / 2, y, w, h, fill=st["fill"], stroke=st["stroke"], rx=rx)
    base = y + pad + FS_TITLE - 0.6
    c.text(cx, base, title, FS_TITLE, weight="bold", fill=st["text"])
    if subs:
        c.lines(cx, base + LH_TITLE - 0.8, subs, FS_SUB, LH_SUB,
                fill=st["text"])
    return y, y + h


def decision(c: Canvas, cx, y, w, title, subs):
    """Diamond node.  Returns (y_top, y_bottom)."""
    st = STYLES["decision"]
    n = 1 + len(subs)
    h = 24 + n * 7.2
    c.diamond(cx, y + h / 2, w, h, fill=st["fill"], stroke=st["stroke"])
    block = FS_DEC + (len(subs) * LH_SUB)
    base = y + h / 2 - block / 2 + FS_DEC - 0.5
    c.text(cx, base, title, FS_DEC, weight="bold", fill=st["text"])
    if subs:
        c.lines(cx, base + LH_TITLE - 1.2, subs, FS_DEC_SUB, LH_SUB,
                fill=st["text"])
    return y, y + h


def vlink(c: Canvas, cx, y0, y1, *, colour=C_DARK, label=None, side="right"):
    """Vertical arrow between two stacked nodes."""
    c.path(f"M {cx:.2f} {y0:.2f} L {cx:.2f} {y1:.2f}", stroke=colour)
    if label:
        dx = 3.2 if side == "right" else -3.2
        anchor = "start" if side == "right" else "end"
        c.text(cx + dx, (y0 + y1) / 2 + 2.0, label, FS_EDGE, weight="bold",
               fill=colour, anchor=anchor)


def hlink(c: Canvas, x0, x1, y, *, colour=C_DARK, label=None, label_dy=-3.0):
    """Horizontal arrow; label_dy lifts the label clear of the target box."""
    c.path(f"M {x0:.2f} {y:.2f} L {x1:.2f} {y:.2f}", stroke=colour)
    if label:
        c.text((x0 + x1) / 2, y + label_dy, label, FS_EDGE, weight="bold",
               fill=colour)


def loop_frame(c: Canvas, x, y, w, h, caption):
    """Dashed container marking a repeated block."""
    c.rect(x, y, w, h, fill="none", stroke=C_LOOP, rx=3.0, sw=STROKE_THIN,
           dash="3.2 2.4")
    c.add(f'<rect x="{x + 6:.2f}" y="{y - 3.6:.2f}" '
          f'width="{len(caption) * 3.05 + 6:.2f}" height="7.4" '
          f'fill="#ffffff" stroke="none"/>')
    c.text(x + 9, y + 2.4, caption, FS_LOOP, fill="#475569", anchor="start",
           style="italic")


def connector(c: Canvas, cx, cy, letter, *, note=None):
    c.circle(cx, cy, 7.4, fill="#ffffff", stroke=C_DARK)
    c.text(cx, cy + 2.6, letter, FS_TITLE, weight="bold", fill=C_DARK)
    if note:
        c.text(cx + 11, cy + 2.2, note, FS_LOOP, fill="#475569",
               anchor="start", style="italic")


def panel_head(c: Canvas, x, y, letter, title):
    c.text(x, y, letter, FS_PANEL, weight="bold", fill="#0f172a",
           anchor="start")
    c.text(x + 11, y, title, FS_PANEL_TITLE, weight="bold", fill="#0f172a",
           anchor="start")


# --------------------------------------------------------------------------
# CONTENT — edit the wording here
# --------------------------------------------------------------------------

def outcome_box(c: Canvas, cx, y, w, lines, kind, glyph=None, h=None):
    """Terminal classification node with an optional symbol below the label."""
    st = STYLES[kind]
    pad = 5.2
    h = h or (pad * 2 + LH_TITLE * len(lines) - 1.6 + 12.0)
    c.rect(cx - w / 2, y, w, h, fill=st["fill"], stroke=st["stroke"], rx=2.0)
    base = y + pad + FS_TITLE - 0.6
    c.lines(cx, base, lines, FS_TITLE, LH_TITLE, weight="bold",
            fill=st["text"])
    if glyph == "star":
        c.star(cx, base + LH_TITLE * (len(lines) - 1) + 8.6, 5.0)
    elif glyph == "cross":
        c.cross(cx, base + LH_TITLE * (len(lines) - 1) + 8.4, 3.6)
    return y, y + h


# --------------------------------------------------------------------------
# CONTENT — edit the wording here
# --------------------------------------------------------------------------

def build() -> Canvas:
    c = Canvas(WIDTH)

    # Column geometry -----------------------------------------------------
    L_X0, L_X1 = 4.0, 254.0              # panel A column
    R_X0, R_X1 = 262.0, WIDTH - 4.0      # panels B and C column

    A_CX, A_W = 82.0, 152.0              # main chain of panel A
    A_SIDE_CX, A_SIDE_W = 204.0, 84.0    # side branches of panel A

    B_CX, B_W = 342.0, 136.0             # main chain of panel B
    B_SIDE_CX, B_SIDE_W = 443.0, 50.0    # discard branch

    C_CX = 371.0                         # main chain of panel C
    C_W = 154.0

    GAP = 10.0                           # vertical gap between stacked nodes

    # ---------------------------------------------------------------- A ---
    y = 13.0
    panel_head(c, L_X0, y, "A", "Locus clustering")
    y += 9.0

    _, y = box(c, A_CX, y, A_W, "Input",
               ["Perfect SSRs mined from all genomes,",
                "processed in file order",
                "(genome 01 = reference)"], "io", rx=7.0)

    loop_top = y + 12.0
    vlink(c, A_CX, y + 1.2, loop_top + 9.0)

    y = loop_top + 12.0
    _, y = box(c, A_CX, y, A_W, "Canonical motif",
               ["smallest rotation of the motif",
                "and of its reverse complement"])

    vlink(c, A_CX, y + 1.2, y + GAP - 2.0)
    y += GAP
    _, y = box(c, A_CX, y, A_W, "Build anchor",
               ["6-mers from the 60 bp of each flank",
                "adjacent to the SSR",
                "(6-mers containing N are discarded)"])

    vlink(c, A_CX, y + 1.2, y + GAP - 2.0)
    y += GAP
    _, y = box(c, A_CX, y, A_W, "Candidate clusters",
               ["existing clusters with the",
                "same canonical motif"])

    inner_top = y + 11.0
    vlink(c, A_CX, y + 1.2, inner_top + 8.5)

    y = inner_top + 11.5
    _, y = box(c, A_CX, y, A_W, "Flank similarity vs. anchor",
               ["overlap coefficient |A∩B| / min(|A|, |B|)",
                "between 6-mer sets, left and right flanks,",
                "forward and reverse-complement orientations",
                "(anchor = founding SSR of the cluster)"])

    vlink(c, A_CX, y + 1.2, y + GAP - 2.0)
    y += GAP
    dec_top, y = decision(c, A_CX, y, 138.0,
                          "≥ 0.6 on every flank",
                          ["with valid 6-mers,",
                           "in either orientation?"])
    mid = (dec_top + y) / 2
    hlink(c, A_CX + 69.0 + 1, A_SIDE_CX - A_SIDE_W / 2 - 1, mid,
          colour=C_NO, label="No", label_dy=-15.5)
    box(c, A_SIDE_CX, mid - 13.0, A_SIDE_W, "Skip candidate",
        ["try the next cluster"], "discard")

    vlink(c, A_CX, y + 1.2, y + GAP + 1.0, colour=C_YES, label="Yes")
    y += GAP + 3.0
    _, y = box(c, A_CX, y, A_W, "Best candidate so far",
               ["kept if the mean similarity is",
                "the highest seen for this SSR"], "io")

    inner_bottom = y + 10.0
    loop_frame(c, L_X0 + 4, inner_top, 246.0, inner_bottom - inner_top,
               "Repeat for each candidate cluster")

    vlink(c, A_CX, y + 1.2, inner_bottom + 9.5)
    y = inner_bottom + 11.5
    dec_top, y = decision(c, A_CX, y, 118.0, "Best candidate found?", [])
    mid = (dec_top + y) / 2
    hlink(c, A_CX + 59.0 + 1, A_SIDE_CX - A_SIDE_W / 2 - 1, mid,
          colour=C_NO, label="No", label_dy=-18.5)
    box(c, A_SIDE_CX, mid - 16.0, A_SIDE_W, "Create new cluster",
        ["this SSR becomes", "its founder"], "updated")

    vlink(c, A_CX, y + 1.2, y + GAP + 1.0, colour=C_YES, label="Yes")
    y += GAP + 3.0
    _, y = box(c, A_CX, y, A_W, "Add SSR to best cluster",
               ["record orientation (+/−)",
                "relative to the founder"], "updated")

    loop_bottom = y + 10.0
    loop_frame(c, L_X0, loop_top, L_X1 - L_X0, loop_bottom - loop_top,
               "Repeat for each SSR")

    vlink(c, A_CX, y + 1.2, loop_bottom + 10.5)
    conn_y = loop_bottom + 19.0
    connector(c, A_CX, conn_y, "B", note="after the last SSR")
    a_bottom = conn_y + 8.0

    # ---------------------------------------------------------------- B ---
    y = 13.0
    panel_head(c, R_X0, y, "B", "Sub-threshold search")
    y += 7.0

    connector(c, B_CX, y + 7.0, "B")
    y += 15.0

    loop_top_b = y + 7.0
    vlink(c, B_CX, y - 1.0, loop_top_b + 9.0)

    y = loop_top_b + 12.0
    _, y = box(c, B_CX, y, B_W, "Loci absent from this genome",
               ["no SSR meeting the threshold here"])

    vlink(c, B_CX, y + 1.2, y + GAP - 2.0)
    y += GAP
    _, y = box(c, B_CX, y, B_W, "Re-mine the whole genome",
               ["relaxed thresholds: ceil(0.6 × minimum",
                "repeat number), never below 3 repeats;",
                "60-bp flanks for the anchors"], "relaxed")

    inner_top_b = y + 11.0
    vlink(c, B_CX, y + 1.2, inner_top_b + 8.5)

    y = inner_top_b + 11.5
    dec_top, y = decision(c, B_CX, y, 130.0, "Overlaps an SSR",
                          ["already annotated", "in this genome?"])
    mid = (dec_top + y) / 2
    hlink(c, B_CX + 65.0 + 1, B_SIDE_CX - B_SIDE_W / 2 - 1, mid,
          colour=C_YES, label="Yes", label_dy=-11.5)
    box(c, B_SIDE_CX, mid - 9.0, B_SIDE_W, "Discard", [], "discard")

    vlink(c, B_CX, y + 1.2, y + GAP + 1.0, colour=C_NO, label="No")
    y += GAP + 3.0
    dec_top, y = decision(c, B_CX, y, 130.0, "Same canonical motif",
                          ["and anchor similarity ≥ 0.6",
                           "with an absent locus?"])
    mid = (dec_top + y) / 2
    hlink(c, B_CX + 65.0 + 1, B_SIDE_CX - B_SIDE_W / 2 - 1, mid,
          colour=C_NO, label="No", label_dy=-11.5)
    box(c, B_SIDE_CX, mid - 9.0, B_SIDE_W, "Discard", [], "discard")

    vlink(c, B_CX, y + 1.2, y + GAP + 1.0, colour=C_YES, label="Yes")
    y += GAP + 3.0
    _, y = box(c, B_CX, y, B_W, "Below-threshold copy",
               ["at the best-matching absent locus",
                "(copy with most repeats kept)"], "updated")

    inner_bottom_b = y + 9.5
    loop_frame(c, R_X0 + 5, inner_top_b, (R_X1 - 5) - (R_X0 + 5),
               inner_bottom_b - inner_top_b, "Repeat for each relaxed hit")
    loop_bottom_b = inner_bottom_b + 6.5
    loop_frame(c, R_X0, loop_top_b, R_X1 - R_X0,
               loop_bottom_b - loop_top_b, "Repeat for each genome")

    # ---------------------------------------------------------------- C ---
    y = loop_bottom_b + 13.0
    panel_head(c, R_X0, y, "C", "Numbering and classification")
    y += 9.0

    # route the B -> C link down the right margin, clear of the heading
    jog = 440.0
    c.path(f"M {B_CX:.2f} {loop_bottom_b + 1.0:.2f} "
           f"L {B_CX:.2f} {loop_bottom_b + 7.0:.2f} "
           f"L {jog:.2f} {loop_bottom_b + 7.0:.2f} "
           f"L {jog:.2f} {y + 1.0:.2f} "
           f"L {C_CX:.2f} {y + 1.0:.2f} "
           f"L {C_CX:.2f} {y + 6.5:.2f}", stroke=C_DARK)
    y += 8.5

    _, y = box(c, C_CX, y, C_W, "Order loci along the reference genome",
               ["loci absent from the reference are placed by",
                "interpolation between shared neighbouring loci;",
                "final IDs SSR.01, SSR.02, …"])

    vlink(c, C_CX, y + 1.2, y + GAP - 2.0)
    y += GAP
    _, y = box(c, C_CX, y, C_W, "Variation type per locus",
               ["Conserved | Length polymorphism |",
                "Below threshold in some species |",
                "Absent in some species"])

    vlink(c, C_CX, y + 1.2, y + GAP - 2.0)
    y += GAP
    dec_top, y = decision(c, C_CX, y, 130.0, "Meets the threshold",
                          ["in only one genome?"])
    mid_1 = (dec_top + y) / 2

    vlink(c, C_CX, y + 1.2, y + GAP + 1.0, colour=C_YES, label="Yes")
    y += GAP + 3.0
    dec_top, y = decision(c, C_CX, y, 130.0, "Below-threshold homolog",
                          ["in another genome?"])
    mid_2 = (dec_top + y) / 2
    dec2_bottom = y

    # three outcomes
    out_y = dec2_bottom + 15.0
    out_w = 62.0
    cx_shared, cx_real, cx_thr = 297.0, C_CX, 444.0

    out_h = 4.8 * 2 + LH_TITLE * 2 - 1.6 + 12.0
    outcome_box(c, cx_shared, out_y, out_w, ["Shared", "locus"], "process",
                h=out_h)
    _, out_bottom = outcome_box(c, cx_real, out_y, out_w,
                                ["Real", "exclusive"], "exclusive", "star",
                                h=out_h)
    outcome_box(c, cx_thr, out_y, out_w, ["Threshold-only", "exclusive"],
                "thresh", "cross", h=out_h)

    c.path(f"M {C_CX - 65.0:.2f} {mid_1:.2f} L {cx_shared:.2f} {mid_1:.2f} "
           f"L {cx_shared:.2f} {out_y - 1.0:.2f}", stroke=C_NO)
    c.text(C_CX - 65.0 - 3.0, mid_1 - 3.4, "No", FS_EDGE, weight="bold",
           fill=C_NO, anchor="end")

    c.path(f"M {C_CX + 65.0:.2f} {mid_2:.2f} L {cx_thr:.2f} {mid_2:.2f} "
           f"L {cx_thr:.2f} {out_y - 1.0:.2f}", stroke=C_YES)
    c.text(C_CX + 65.0 + 3.0, mid_2 - 3.4, "Yes", FS_EDGE, weight="bold",
           fill=C_YES, anchor="start")

    vlink(c, C_CX, dec2_bottom + 1.2, out_y - 1.0, colour=C_NO, label="No")

    # output
    y = out_bottom + 13.0
    bus = y - 6.0
    for x in (cx_shared, cx_thr):
        c.path(f"M {x:.2f} {out_bottom + 1.0:.2f} L {x:.2f} {bus:.2f}",
               stroke=C_DARK, marker=False)
    c.path(f"M {cx_shared:.2f} {bus:.2f} L {cx_thr:.2f} {bus:.2f}",
           stroke=C_DARK, marker=False)
    c.path(f"M {cx_real:.2f} {out_bottom + 1.0:.2f} "
           f"L {cx_real:.2f} {y - 1.0:.2f}", stroke=C_DARK)

    _, y = box(c, C_CX, y, 208.0, "Output",
               ["loci with IDs, coordinates, orientation, variation type,",
                "exclusivity class and N-in-flank (compromised) flags"],
               "io", rx=7.0)
    c_bottom = y

    # ----------------------------------------------------------- legend ---
    leg_y = a_bottom + 14.0
    leg_h = 72.0
    c.rect(L_X0, leg_y, L_X1 - L_X0, leg_h, fill="#ffffff", stroke="#cbd5e1",
           rx=3.0, sw=STROKE_THIN)
    c.text(L_X0 + 9, leg_y + 12.0, "Legend", FS_TITLE, weight="bold",
           fill="#0f172a", anchor="start")

    col1 = L_X0 + 9
    col2 = L_X0 + 126
    row0 = leg_y + 24.0
    step = 11.2
    sw_w, sw_h = 13.0, 7.4

    def swatch(x, yy, kind, label):
        st = STYLES[kind]
        c.rect(x, yy - sw_h + 1.0, sw_w, sw_h, fill=st["fill"],
               stroke=st["stroke"], rx=1.2, sw=STROKE_THIN)
        c.text(x + sw_w + 4.5, yy, label, FS_LEGEND, fill="#334155",
               anchor="start")

    swatch(col1, row0 + 0 * step, "io", "Input / output / candidate")
    swatch(col1, row0 + 1 * step, "process", "Process")
    swatch(col1, row0 + 2 * step, "updated", "Locus updated")
    swatch(col1, row0 + 3 * step, "relaxed", "Relaxed-threshold search")
    swatch(col1, row0 + 4 * step, "discard", "Candidate or hit discarded")

    st = STYLES["decision"]
    c.diamond(col2 + sw_w / 2, row0 - 2.0, sw_w + 2, sw_h + 1.6,
              fill=st["fill"], stroke=st["stroke"], sw=STROKE_THIN)
    c.text(col2 + sw_w + 4.5, row0, "Decision", FS_LEGEND, fill="#334155",
           anchor="start")

    c.rect(col2, row0 + step - sw_h + 1.0, sw_w, sw_h, fill="none",
           stroke=C_LOOP, rx=1.2, sw=STROKE_THIN, dash="2.4 1.8")
    c.text(col2 + sw_w + 4.5, row0 + step, "Repeated step (loop)", FS_LEGEND,
           fill="#334155", anchor="start")

    c.path(f"M {col2:.2f} {row0 + 2 * step - 2.2:.2f} "
           f"L {col2 + sw_w:.2f} {row0 + 2 * step - 2.2:.2f}", stroke=C_YES,
           sw=STROKE_THIN)
    c.text(col2 + sw_w + 4.5, row0 + 2 * step, "Yes branch", FS_LEGEND,
           fill="#334155", anchor="start")
    c.path(f"M {col2:.2f} {row0 + 3 * step - 2.2:.2f} "
           f"L {col2 + sw_w:.2f} {row0 + 3 * step - 2.2:.2f}", stroke=C_NO,
           sw=STROKE_THIN)
    c.text(col2 + sw_w + 4.5, row0 + 3 * step, "No branch", FS_LEGEND,
           fill="#334155", anchor="start")

    c.star(col2 + sw_w / 2, row0 + 4 * step - 2.2, 4.6)
    c.text(col2 + sw_w + 4.5, row0 + 4 * step, "Real exclusive marker",
           FS_LEGEND, fill="#334155", anchor="start")

    c.cross(col2 + sw_w / 2, row0 + 5 * step - 2.2, 3.2)
    c.text(col2 + sw_w + 4.5, row0 + 5 * step, "Threshold-only exclusive",
           FS_LEGEND, fill="#334155", anchor="start")

    c.height = max(leg_y + leg_h, c_bottom) + 10.0
    return c


# --------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Build Figure 1 of the THANNYA "
                                             "manuscript.")
    ap.add_argument("-o", "--out", default=None,
                    help="output basename (default: fig1_workflow)")
    ap.add_argument("--pdf", action="store_true",
                    help="also write a vector PDF (requires cairosvg)")
    ap.add_argument("--png", action="store_true",
                    help="also write a raster proof (requires cairosvg)")
    ap.add_argument("--dpi", type=float, default=600.0,
                    help="resolution of the raster proof (default: 600)")
    args = ap.parse_args()

    base = args.out or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "fig1_workflow")
    canvas = build()
    svg = canvas.render()

    with open(base + ".svg", "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"wrote {base}.svg  "
          f"({WIDTH_MM:.0f} x {canvas.height / PT_PER_MM:.1f} mm)")

    if args.pdf or args.png:
        try:
            import cairosvg
        except ImportError:
            raise SystemExit("cairosvg is required for --pdf/--png: "
                             "pip install cairosvg")
        if args.pdf:
            cairosvg.svg2pdf(bytestring=svg.encode("utf-8"),
                             write_to=base + ".pdf")
            print(f"wrote {base}.pdf")
        if args.png:
            # size the raster from the physical width so --dpi means what
            # it says, whatever unit conversion cairosvg defaults to
            px = int(round(WIDTH_MM / 25.4 * args.dpi))
            cairosvg.svg2png(bytestring=svg.encode("utf-8"),
                             write_to=base + ".png", output_width=px)
            print(f"wrote {base}.png ({px} px wide, {args.dpi:.0f} dpi "
                  f"at {WIDTH_MM:.0f} mm)")


if __name__ == "__main__":
    main()
