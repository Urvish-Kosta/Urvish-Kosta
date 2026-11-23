#!/usr/bin/env python3
"""
circuit_bloom.py

Same generative hex L-system as scripts/circuit_bloom.py, plus a SMIL
"energize" sweep: traces draw themselves outward from the centre die,
depth by depth, then vias and tip-pads light up behind the wavefront.
The whole thing loops on a fixed period so a visitor who lingers sees it
more than once.

Technique: every <line> gets stroke-dasharray = its own length and an
<animate> on stroke-dashoffset driven by values/keyTimes over one shared
LOOP period. keyTimes hold the line hidden until its slot, draw it, then
hold it lit until the loop restarts. One animate element per line, no JS.

Usage:  python3 scripts/circuit_bloom.py [seed]
"""
import math
import random
import sys
import datetime

# --- animation tuning -------------------------------------------------
LOOP = 14.0        # seconds for one full cycle
DEPTH_STEP = 0.45  # delay added per L-system depth
DRAW = 0.85        # seconds a single trace takes to draw
FADE = 0.5         # seconds for a via / pad to fade in
# ----------------------------------------------------------------------


def kt(t):
    """clamp a time in seconds to a keyTimes fraction of the loop"""
    return max(0.0, min(1.0, t / LOOP))


def make_svg(seed):
    random.seed(seed)

    W = H = 820
    CX, CY = W / 2, H / 2

    lines = []
    vias = []

    def branch(x, y, angle, length, depth, max_depth):
        if depth > max_depth or length < 8:
            return
        x2 = x + length * math.cos(angle)
        y2 = y + length * math.sin(angle)
        lines.append((x, y, x2, y2, depth))
        if depth < max_depth:
            vias.append((x2, y2, depth))
        n_children = 2 if depth < max_depth - 1 else random.choice([1, 2])
        spread = math.radians(random.uniform(22, 40))
        for i in range(n_children):
            if n_children == 1:
                da = random.uniform(-0.35, 0.35)
            else:
                da = spread * (i - (n_children - 1) / 2) / max(1, (n_children - 1)) * 2
                da += random.uniform(-0.08, 0.08)
            new_len = length * random.uniform(0.62, 0.72)
            branch(x2, y2, angle + da, new_len, depth + 1, max_depth)

    n_spokes = random.choice([5, 6, 7])
    max_depth = 4
    for i in range(n_spokes):
        a = (2 * math.pi / n_spokes) * i + math.radians(random.uniform(-4, 4))
        branch(CX, CY, a, 105, 0, max_depth)

    palette = ["#58a6ff", "#4f9ee0", "#46c2b0", "#3fb950", "#7bc96f", "#d2c34a", "#d29922"]

    def color_for_depth(d, maxd):
        idx = min(int(d / maxd * (len(palette) - 1)), len(palette) - 1)
        return palette[idx]

    # when the wavefront reaches each depth
    def slot(depth):
        start = 0.35 + depth * DEPTH_STEP
        return start, start + DRAW

    sweep_end = slot(max_depth)[1] + FADE

    p = []
    p.append(f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg" font-family="\'Fira Code\',monospace">')
    p.append('<defs>')
    p.append('<pattern id="g2" width="22" height="22" patternUnits="userSpaceOnUse">')
    p.append('<path d="M 22 0 L 0 0 0 22" fill="none" stroke="#30363d" stroke-width="0.4" opacity="0.3"/>')
    p.append('</pattern>')
    p.append('<radialGradient id="glow" cx="50%" cy="50%" r="50%">')
    p.append('<stop offset="0%" stop-color="#58a6ff" stop-opacity="0.35"/>')
    p.append('<stop offset="100%" stop-color="#58a6ff" stop-opacity="0"/>')
    p.append('</radialGradient>')
    p.append('</defs>')
    p.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#0d1117"/>')
    p.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="url(#g2)"/>')

    # centre glow pulses in sync with the sweep
    p.append(f'<circle cx="{CX}" cy="{CY}" r="230" fill="url(#glow)" opacity="0.25">')
    p.append(f'  <animate attributeName="opacity" dur="{LOOP}s" repeatCount="indefinite" '
             f'values="0.15;0.55;0.3;0.3;0.15" '
             f'keyTimes="0;{kt(0.5):.4f};{kt(sweep_end):.4f};{kt(LOOP-1.2):.4f};1"/>')
    p.append('</circle>')

    # --- traces: draw-on via stroke-dashoffset ---
    for (x1, y1, x2, y2, d) in lines:
        c = color_for_depth(d, max_depth)
        w = max(0.6, 2.6 - d * 0.35)
        op = max(0.35, 1 - d * 0.10)
        L = math.hypot(x2 - x1, y2 - y1)
        t0, t1 = slot(d)
        t0 += random.uniform(-0.06, 0.06)   # slight jitter so it isn't a rigid ring
        t1 += random.uniform(-0.06, 0.06)
        p.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{c}" stroke-width="{w:.2f}" opacity="{op:.2f}" stroke-linecap="round" '
            f'stroke-dasharray="{L:.2f}" stroke-dashoffset="{L:.2f}">'
        )
        p.append(
            f'  <animate attributeName="stroke-dashoffset" dur="{LOOP}s" repeatCount="indefinite" '
            f'values="{L:.2f};{L:.2f};0;0" '
            f'keyTimes="0;{kt(t0):.4f};{kt(t1):.4f};1" '
            f'calcMode="spline" keySplines="0 0 1 1;.25 .1 .25 1;0 0 1 1"/>'
        )
        p.append('</line>')

    # --- vias: fade in just behind the wavefront ---
    for (x, y, d) in vias:
        c = color_for_depth(d, max_depth)
        r = max(1.0, 2.6 - d * 0.3)
        t1 = slot(d)[1]
        p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="{c}" opacity="0">')
        p.append(
            f'  <animate attributeName="opacity" dur="{LOOP}s" repeatCount="indefinite" '
            f'values="0;0;0.85;0.85" keyTimes="0;{kt(t1):.4f};{kt(t1+FADE):.4f};1"/>'
        )
        p.append('</circle>')

    # --- tip pads: fade in last, then breathe ---
    tips = [(x2, y2) for (x1, y1, x2, y2, d) in lines if d == max_depth]
    t_tip = slot(max_depth)[1]
    for (x, y) in tips:
        p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="none" stroke="#d29922" stroke-width="1" opacity="0">')
        p.append(
            f'  <animate attributeName="opacity" dur="{LOOP}s" repeatCount="indefinite" '
            f'values="0;0;0.75;0.35;0.6;0.6" '
            f'keyTimes="0;{kt(t_tip):.4f};{kt(t_tip+FADE):.4f};'
            f'{kt(t_tip+FADE+2.5):.4f};{kt(t_tip+FADE+5.0):.4f};1"/>'
        )
        p.append('</circle>')

    # --- the die at the centre: always on, powers up first ---
    p.append(f'<circle cx="{CX}" cy="{CY}" r="10" fill="#0d1117" stroke="#58a6ff" stroke-width="2"/>')
    p.append(f'<circle cx="{CX}" cy="{CY}" r="4" fill="#58a6ff">')
    p.append(f'  <animate attributeName="r" dur="{LOOP}s" repeatCount="indefinite" '
             f'values="4;6.5;4;4" keyTimes="0;{kt(0.35):.4f};{kt(1.1):.4f};1"/>')
    p.append('</circle>')

    # --- packet dots: unchanged idea, but held back until the board is lit ---
    random.shuffle(lines)
    sample = lines[:7]
    colors_cycle = ["#7ee787", "#f2cc60", "#79c0ff"]
    for i, (x1, y1, x2, y2, d) in enumerate(sample):
        col = colors_cycle[i % len(colors_cycle)]
        dur = round(random.uniform(2.2, 4.0), 2)
        begin = round(sweep_end + random.uniform(0, 2.5), 2)
        p.append(f'<circle r="2.4" fill="{col}" opacity="0">')
        p.append(f'  <animateMotion dur="{dur}s" begin="{begin}s" repeatCount="indefinite" '
                 f'path="M{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f}"/>')
        p.append(f'  <set attributeName="opacity" to="1" begin="{begin}s"/>')
        p.append('</circle>')

    p.append(f'<text x="{W-14}" y="{H-14}" text-anchor="end" font-size="9" fill="#484f58" letter-spacing="1">'
             f'// circuit_bloom.py — seed:{seed} — spokes:{n_spokes} — regenerated daily</text>')
    p.append('</svg>')
    return "\n".join(p)


if __name__ == "__main__":
    seed = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().strftime("%Y%m%d")
    out = sys.argv[2] if len(sys.argv) > 2 else "assets/circuit-bloom.svg"
    with open(out, "w") as f:
        f.write(make_svg(seed))
    print(f"generated {out} with seed {seed}")
