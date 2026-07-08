#!/usr/bin/env python3
"""
hacker_pun.py

Picks a hardware/coding pun deterministically by date and renders it as a
small banner SVG. Regenerated daily via GitHub Actions -- new pun every day,
same file path, so the README embed always shows today's pun.
"""
import datetime

PUNS = [
    "I've got a lot of unresolved ohm-issues.",
    "Why did the FPGA and the ASIC break up? Too many fixed opinions.",
    "I'm on a strict capacitor diet -- can't handle too much current.",
    "My PCBs don't have bugs, they have undocumented short circuits.",
    "I used to be a JTAG connector, but I lost my grip on things.",
    "Resistance is futile. Voltage, on the other hand, is very persuasive.",
    "I'm reading your signals loud and clear -- mostly noise, though.",
    "Electrons never get lost. They just follow the path of least resistance.",
    "My code review's on hold -- too many pull requests, not enough pull-ups.",
    "I'm not procrastinating, I'm just waiting on a clock domain crossing.",
    "There are 10 types of people: those who understand binary, and those who don't.",
    "I tried debugging my life. Turns out it was a hardware problem.",
    "My love life is like my breadboard -- a lot of loose connections.",
    "The transistor skipped the party. Wasn't feeling too switched on.",
    "I don't always test my code, but when I do, I test in the simulator first.",
    "Asked my multimeter for relationship advice. It just said 'open circuit'.",
    "I'm fluent in two languages: English, and passive-aggressive commit messages.",
    "My FPGA and I have a lot in common -- we both reconfigure under pressure.",
    "I once tried to overclock my sleep schedule. Thermal throttled immediately.",
    "Some people count sheep. I count clock cycles.",
    "My favorite exercise is jumping to conclusions about why the board won't boot.",
    "I'm not saying it's a grounding issue. I'm saying everything is, eventually.",
    "Good engineers don't fear silence -- they fear an unterminated bus.",
    "I speak SPI, I2C, and fluent sarcasm.",
]

def make_svg(seed):
    idx = int(seed) % len(PUNS)
    pun = PUNS[idx]
    W, H = 900, 70
    # rough width estimate for Fira Code at 15px: ~9px/char
    max_line_chars = 88
    if len(pun) > max_line_chars:
        # split on nearest space before limit
        cut = pun.rfind(" ", 0, max_line_chars)
        line1, line2 = pun[:cut], pun[cut+1:]
        H = 90
    else:
        line1, line2 = pun, None

    p = []
    p.append(f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg" font-family="\'Fira Code\',monospace">')
    p.append(f'<rect x="0" y="0" width="{W}" height="{H}" rx="6" fill="#0d1117" stroke="#30363d" stroke-width="1"/>')
    p.append(f'<rect x="0" y="0" width="5" height="{H}" rx="2" fill="#d29922"/>')
    p.append(f'<text x="26" y="22" font-size="10" fill="#d29922" letter-spacing="2">PUN OF THE DAY</text>')
    if line2:
        p.append(f'<text x="26" y="44" font-size="14" fill="#c9d1d9">{line1}</text>')
        p.append(f'<text x="26" y="64" font-size="14" fill="#c9d1d9">{line2}</text>')
    else:
        p.append(f'<text x="26" y="48" font-size="14" fill="#c9d1d9">{line1}</text>')
    p.append('</svg>')
    return "\n".join(p), H

if __name__ == "__main__":
    seed = datetime.date.today().toordinal()
    svg, h = make_svg(seed)
    with open("assets/hacker-pun.svg", "w") as f:
        f.write(svg)
    print(f"generated assets/hacker-pun.svg (seed {seed}, height {h})")
