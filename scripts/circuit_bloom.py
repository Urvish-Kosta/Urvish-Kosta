#!/usr/bin/env python3
"""
circuit-bloom.py

A tiny generative art script. Grows a radially-symmetric hex L-system
that looks like PCB fan-out traces, colored on a blue->green->amber ramp.
Seeded by the date, so the piece is different every day.

No practical purpose whatsoever. That's the point.
"""
import math
import random
import sys
import datetime

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
    p.append(f'<circle cx="{CX}" cy="{CY}" r="230" fill="url(#glow)"/>')

    for (x1, y1, x2, y2, d) in lines:
        c = color_for_depth(d, max_depth)
        w = max(0.6, 2.6 - d * 0.35)
        op = max(0.35, 1 - d * 0.10)
        p.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{c}" stroke-width="{w:.2f}" opacity="{op:.2f}" stroke-linecap="round"/>')

    for (x, y, d) in vias:
        c = color_for_depth(d, max_depth)
        r = max(1.0, 2.6 - d * 0.3)
        p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="{c}" opacity="0.85"/>')

    tips = [(x2, y2) for (x1, y1, x2, y2, d) in lines if d == max_depth]
    for (x, y) in tips:
        p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="none" stroke="#d29922" stroke-width="1" opacity="0.6"/>')

    p.append(f'<circle cx="{CX}" cy="{CY}" r="10" fill="#0d1117" stroke="#58a6ff" stroke-width="2"/>')
    p.append(f'<circle cx="{CX}" cy="{CY}" r="4" fill="#58a6ff"/>')

    random.shuffle(lines)
    sample = lines[:7]
    colors_cycle = ["#7ee787", "#f2cc60", "#79c0ff"]
    for i, (x1, y1, x2, y2, d) in enumerate(sample):
        col = colors_cycle[i % len(colors_cycle)]
        dur = round(random.uniform(2.2, 4.0), 2)
        begin = round(random.uniform(0, 2.5), 2)
        p.append(f'<circle r="2.4" fill="{col}"><animateMotion dur="{dur}s" begin="{begin}s" repeatCount="indefinite" path="M{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f}"/></circle>')

    p.append(f'<text x="{W-14}" y="{H-14}" text-anchor="end" font-size="9" fill="#484f58" letter-spacing="1">// circuit_bloom.py — seed:{seed} — spokes:{n_spokes} — regenerated daily</text>')
    p.append('</svg>')
    return "\n".join(p)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        seed = sys.argv[1]
    else:
        seed = datetime.date.today().strftime("%Y%m%d")
    svg = make_svg(seed)
    with open("assets/circuit-bloom.svg", "w") as f:
        f.write(svg)
    print(f"generated assets/circuit-bloom.svg with seed {seed}")
