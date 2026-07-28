"""instruction of the day — an animated 5-stage RISC-V pipeline SVG.

Date-seeded: a different real instruction each day, with concrete register
values, walked through IF -> ID -> EX -> MEM -> WB by a moving data packet.
Animation is pure SMIL (time-based, autoplay) so it runs when the SVG is
embedded as an <img> on a GitHub README. No JS, no external deps.

Usage:  python scripts/pipeline.py [YYYY-MM-DD]
Output: assets/pipeline-of-the-day.svg
"""
import os
import sys
import random
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

# palette (matches the profile)
BG = "#0d1117"
PANEL = "#161b22"
BORDER = "#21262d"
FG = "#c9d1d9"
MUTE = "#8b949e"
ACCENT = "#58a6ff"
GLOW = "#58a6ff"
GREEN = "#3fb950"
AMBER = "#d29922"
FONT = "Fira Code, ui-monospace, SFMono-Regular, Menlo, monospace"

STAGES = ["IF", "ID", "EX", "MEM", "WB"]
STAGE_FULL = ["fetch", "decode", "execute", "memory", "write-back"]

# shared animation timeline: 5 dwell points, hold-then-move
KEYTIMES = "0;0.12;0.25;0.37;0.5;0.62;0.75;0.84;0.92;1"
DUR = "9s"

# When FRAME is an int 0..4, emit a STATIC snapshot frozen on that stage
# (for PNG previews only — the real asset keeps the SMIL animation). -1 = animate.
FRAME = -1


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def opacity_values(active):
    """Return a 10-point values string that is 1 only while stage `active`
    holds the packet (positions 2*active and 2*active+1), 0 otherwise."""
    v = ["0"] * 10
    v[2 * active] = "1"
    v[2 * active + 1] = "1"
    return ";".join(v)


def anim_opacity(active, extra=""):
    if FRAME >= 0:
        # static snapshot: no <animate>; caller sets element opacity via helper
        return ""
    return (f'<animate attributeName="opacity" values="{opacity_values(active)}" '
            f'keyTimes="{KEYTIMES}" dur="{DUR}" repeatCount="indefinite" {extra}/>')


def op0(active):
    """Initial opacity for an element tied to `active` stage (1 if this is the
    frozen frame, else 0). Keeps animated build unchanged."""
    return "1" if (FRAME >= 0 and FRAME == active) else "0"


def todays_instruction(datestr):
    seed = int(datestr.replace("-", ""))
    rng = random.Random(seed)

    def reg():
        return rng.randint(1, 15)

    def val():
        return rng.randint(1, 40)

    kind = rng.choice(["add", "sub", "and", "or", "sll", "addi", "lw", "sw", "beq"])
    rs1, rs2, rd = reg(), reg(), reg()
    while rs2 == rs1:          # distinct source registers read cleanly
        rs2 = reg()
    while rd in (0,):
        rd = reg()
    v1, v2 = val(), val()

    if kind in ("add", "sub", "and", "or", "sll"):
        ops = {"add": ("+", v1 + v2), "sub": ("-", v1 - v2),
               "and": ("&", v1 & v2), "or": ("|", v1 | v2),
               "sll": ("<<", v1 << (v2 % 5))}
        sym, res = ops[kind]
        v2disp = (v2 % 5) if kind == "sll" else v2
        return {
            "asm": f"{kind} x{rd}, x{rs1}, x{rs2}",
            "note": "R-type · register-register ALU op",
            "id": f"read x{rs1}={v1}, x{rs2}={v2disp}",
            "ex": f"ALU: {v1} {sym} {v2disp} = {res}",
            "mem": "(no memory access)",
            "wb": f"x{rd} <- {res}",
            "packet": ["PC", f"x{rs1},x{rs2}", str(res), "--", f"x{rd}"],
            "date": datestr,
        }
    if kind == "addi":
        imm = rng.randint(-8, 16)
        res = v1 + imm
        return {
            "asm": f"addi x{rd}, x{rs1}, {imm}",
            "note": "I-type · add immediate",
            "id": f"read x{rs1}={v1}, imm={imm}",
            "ex": f"ALU: {v1} + ({imm}) = {res}",
            "mem": "(no memory access)",
            "wb": f"x{rd} <- {res}",
            "packet": ["PC", f"x{rs1},imm", str(res), "--", f"x{rd}"],
            "date": datestr,
        }
    if kind == "lw":
        imm = rng.randint(0, 32)
        addr = v1 + imm
        memval = val() * 2
        return {
            "asm": f"lw x{rd}, {imm}(x{rs1})",
            "note": "I-type · load word from data memory",
            "id": f"read base x{rs1}={v1}, imm={imm}",
            "ex": f"addr = {v1} + {imm} = {addr}",
            "mem": f"load M[{addr}] = {memval}",
            "wb": f"x{rd} <- {memval}",
            "packet": ["PC", f"x{rs1},imm", str(addr), str(memval), f"x{rd}"],
            "date": datestr,
        }
    if kind == "sw":
        imm = rng.randint(0, 32)
        addr = v1 + imm
        return {
            "asm": f"sw x{rs2}, {imm}(x{rs1})",
            "note": "S-type · store word to data memory",
            "id": f"read x{rs1}={v1}, x{rs2}={v2}",
            "ex": f"addr = {v1} + {imm} = {addr}",
            "mem": f"store {v2} -> M[{addr}]",
            "wb": "(no write-back)",
            "packet": ["PC", f"x{rs1},x{rs2}", str(addr), f"M<-{v2}", "--"],
            "date": datestr,
        }
    # beq
    off = rng.choice([-16, -8, 8, 16, 24])
    taken = v1 == v2
    return {
        "asm": f"beq x{rs1}, x{rs2}, {off}",
        "note": "B-type · branch if equal",
        "id": f"read x{rs1}={v1}, x{rs2}={v2}",
        "ex": f"{v1} == {v2}? -> {'taken' if taken else 'not taken'}",
        "mem": "(no memory access)",
        "wb": "(no write-back)",
        "packet": ["PC", f"x{rs1},x{rs2}", "cmp", "--", "PC+off" if taken else "PC+4"],
        "date": datestr,
    }


def build_svg(ins):
    W, H = 940, 440
    centers = [100, 280, 460, 640, 820]
    bx_w, bx_h, bx_y = 120, 78, 150
    line_y = bx_y + bx_h + 30   # data-bus lane sits below the stage boxes

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img">',
        f'<rect width="{W}" height="{H}" rx="16" fill="{BG}"/>',
        f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="15" fill="none" '
        f'stroke="{BORDER}"/>',
        # glow filter for the moving packet
        '<defs><filter id="g" x="-50%" y="-50%" width="200%" height="200%">'
        '<feGaussianBlur stdDeviation="4" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
        '</filter></defs>',
    ]

    # header
    parts.append(
        f'<text x="34" y="42" font-size="18" fill="{ACCENT}" font-family="{FONT}" '
        f'font-weight="700">// instruction of the day</text>')
    parts.append(
        f'<text x="34" y="70" font-size="24" fill="{FG}" font-family="{FONT}" '
        f'font-weight="700">{esc(ins["asm"])}</text>')
    parts.append(
        f'<text x="34" y="94" font-size="12" fill="{MUTE}" font-family="{FONT}">'
        f'{esc(ins["note"])} · {esc(ins["date"])}</text>')

    # datapath baseline
    parts.append(
        f'<line x1="{centers[0]}" y1="{line_y}" x2="{centers[-1]}" y2="{line_y}" '
        f'stroke="{BORDER}" stroke-width="2"/>')
    # arrows between stages (along the bus)
    for a, b in zip(centers, centers[1:]):
        mx = (a + b) // 2
        parts.append(
            f'<path d="M{mx-6} {line_y-5} L{mx+4} {line_y} L{mx-6} {line_y+5}" '
            f'fill="{MUTE}"/>')
    # short drop connectors from each stage box down into the bus
    for cx in centers:
        parts.append(
            f'<line x1="{cx}" y1="{bx_y+bx_h}" x2="{cx}" y2="{line_y}" '
            f'stroke="{BORDER}" stroke-width="1.5"/>'
            f'<circle cx="{cx}" cy="{line_y}" r="3" fill="{MUTE}"/>')

    # stage boxes + per-stage glow overlay (opacity animated)
    for i, (cx, name, full) in enumerate(zip(centers, STAGES, STAGE_FULL)):
        x = cx - bx_w // 2
        parts.append(
            f'<rect x="{x}" y="{bx_y}" width="{bx_w}" height="{bx_h}" rx="10" '
            f'fill="{PANEL}" stroke="{BORDER}" stroke-width="1.5"/>')
        # animated glow border (lit while packet is in this stage)
        parts.append(
            f'<rect x="{x}" y="{bx_y}" width="{bx_w}" height="{bx_h}" rx="10" '
            f'fill="none" stroke="{GLOW}" stroke-width="2.5" opacity="{op0(i)}">'
            f'{anim_opacity(i)}</rect>')
        parts.append(
            f'<text x="{cx}" y="{bx_y+34}" text-anchor="middle" font-size="20" '
            f'fill="{FG}" font-family="{FONT}" font-weight="700">{name}</text>')
        parts.append(
            f'<text x="{cx}" y="{bx_y+58}" text-anchor="middle" font-size="11" '
            f'fill="{MUTE}" font-family="{FONT}">{full}</text>')

    # moving data packet (a glowing chip that translates along the pipeline)
    d = [c - centers[0] for c in centers]
    tvals = f'{d[0]},0;{d[0]},0;{d[1]},0;{d[1]},0;{d[2]},0;{d[2]},0;{d[3]},0;{d[3]},0;{d[4]},0;{d[4]},0'
    start_cx = centers[FRAME] if FRAME >= 0 else centers[0]
    parts.append(f'<g transform="translate({start_cx},{line_y})">')
    if FRAME < 0:
        parts.append(
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="{tvals}" keyTimes="{KEYTIMES}" dur="{DUR}" '
            f'repeatCount="indefinite"/>')
    parts.append(
        f'<circle cx="0" cy="0" r="17" fill="{ACCENT}" opacity="0.9" filter="url(#g)"/>')
    # packet label morphs per stage
    for i, lbl in enumerate(ins["packet"]):
        parts.append(
            f'<text x="0" y="{40}" text-anchor="middle" font-size="11" '
            f'fill="{ACCENT}" font-family="{FONT}" font-weight="700" opacity="{op0(i)}">'
            f'{esc(lbl)}{anim_opacity(i)}</text>')
    parts.append('</g>')

    # explanation line that changes as the packet advances
    cap_y = 350
    parts.append(
        f'<rect x="34" y="{cap_y-24}" width="{W-68}" height="46" rx="10" '
        f'fill="{PANEL}" stroke="{BORDER}"/>')
    captions = [
        f'IF  · fetch instruction from I-memory at PC',
        f'ID  · {ins["id"]}',
        f'EX  · {ins["ex"]}',
        f'MEM · {ins["mem"]}',
        f'WB  · {ins["wb"]}',
    ]
    colors = [MUTE, FG, GREEN, AMBER, ACCENT]
    for i, (cap, col) in enumerate(zip(captions, colors)):
        parts.append(
            f'<text x="52" y="{cap_y+5}" font-size="14" fill="{col}" '
            f'font-family="{FONT}" opacity="{op0(i)}">{esc(cap)}{anim_opacity(i)}</text>')

    # footer hint
    parts.append(
        f'<text x="34" y="{H-24}" font-size="11" fill="{MUTE}" font-family="{FONT}">'
        f'a real RISC-V instruction, executed one stage at a time — '
        f'refresh tomorrow for a new one</text>')

    parts.append('</svg>')
    return "".join(parts)


def main():
    os.makedirs(ASSETS, exist_ok=True)
    datestr = sys.argv[1] if len(sys.argv) > 1 else datetime.datetime.utcnow().strftime("%Y-%m-%d")
    ins = todays_instruction(datestr)
    out = os.path.join(ASSETS, "pipeline-of-the-day.svg")
    with open(out, "w", encoding="utf-8") as f:
        f.write(build_svg(ins))
    print(f"{datestr}: {ins['asm']}  |  {ins['ex']}  ->  {ins['wb']}")


if __name__ == "__main__":
    main()
