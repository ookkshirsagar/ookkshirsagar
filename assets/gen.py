#!/usr/bin/env python3
"""Generates assets/{header,skills,footer}.svg (+ -light variants) and assets/isaac.svg.

header: name + RGB-D scan -> 6D pose -> arm + five-finger hand doing power / tripod / pinch grasps (IK-driven).
skills: CV skills as a ROS 2 node graph with animated messages.
footer: two arms cooperatively carrying one object (closed-chain IK).
"""
import math, os, random

# GitHub dark / light palettes; README picks one per viewer theme via <picture>
THEMES = {
    "dark": dict(BG="#0d1117", FG="#c9d1d9", MUTED="#8b949e", DIM="#30363d", ACC="#58e1ff",
                 RX="#ff6b6b", GY="#7ee787", BZ="#79c0ff", BOX="#151b23", EDGE="#3d444d", PANEL="none"),
    "light": dict(BG="#ffffff", FG="#1f2328", MUTED="#59636e", DIM="#d1d9e0", ACC="#0b84b0",
                  RX="#cf222e", GY="#1a7f37", BZ="#0969da", BOX="#f6f8fa", EDGE="#c4ccd5", PANEL="#d1d9e0"),
}


def set_theme(name):
    globals().update(THEMES[name])


def panel(W, H):
    return f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1:.0f}" rx="14" fill="{BG}" stroke="{PANEL}"/>'


set_theme("dark")
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def set_samples(n):
    global ts, KT
    ts = [i / n for i in range(n + 1)]
    KT = ";".join(f"{t:.5f}" for t in ts)


# ---------- helpers ----------
def smooth(a, b, u):
    if u <= a:
        return 0.0
    if u >= b:
        return 1.0
    s = (u - a) / (b - a)
    return s * s * (3 - 2 * s)


def lerp(p, q, s):
    return (p[0] + (q[0] - p[0]) * s, p[1] + (q[1] - p[1]) * s)


def heading(dx, dy):
    """Angle [rad] of a direction in the convention 'link along -y, rotate clockwise'."""
    return math.atan2(dx, -dy)


def ik2(base, wrist, l1, l2, elbow):
    dx, dy = wrist[0] - base[0], wrist[1] - base[1]
    r = math.hypot(dx, dy)
    c = max(-1.0, min(1.0, (r * r - l1 * l1 - l2 * l2) / (2 * l1 * l2)))
    q2 = elbow * math.acos(c)
    q1 = heading(dx, dy) - math.atan2(l2 * math.sin(q2), l1 + l2 * math.cos(q2))
    return q1, q2


def unwrap(seq):
    out = [seq[0]]
    for v in seq[1:]:
        while v - out[-1] > 180:
            v -= 360
        while v - out[-1] < -180:
            v += 360
        out.append(v)
    return out


def rot(series, dur):
    v = ";".join(f"{a:.2f}" for a in series)
    return (f'<animateTransform attributeName="transform" type="rotate" dur="{dur}s" repeatCount="indefinite" '
            f'calcMode="linear" keyTimes="{KT}" values="{v}"/>')


def trans(series, dur):
    v = ";".join(f"{x:.2f},{y:.2f}" for x, y in series)
    return (f'<animateTransform attributeName="transform" type="translate" dur="{dur}s" repeatCount="indefinite" '
            f'calcMode="linear" keyTimes="{KT}" values="{v}"/>')


def attr(name, series, dur, fmt="{:.3f}"):
    v = ";".join(fmt.format(a) for a in series)
    return (f'<animate attributeName="{name}" dur="{dur}s" repeatCount="indefinite" '
            f'calcMode="linear" keyTimes="{KT}" values="{v}"/>')


def frame(s=14, op=0.6):
    return (f'<line x2="{s}" stroke="{RX}" stroke-width="1.2" opacity="{op}"/>'
            f'<line y2="-{s}" stroke="{GY}" stroke-width="1.2" opacity="{op}"/>')


# industrial shell shading: white cover, dark actuator hubs, carbon pads
EDGE_D = "#1b2128"
DEFS = """<linearGradient id="shell" x1="0" x2="1"><stop offset="0" stop-color="#f6f8fa"/>
  <stop offset=".55" stop-color="#d0d7de"/><stop offset="1" stop-color="#8c959f"/></linearGradient>
  <linearGradient id="shellD" x1="0" x2="1"><stop offset="0" stop-color="#b6bfc8"/>
  <stop offset="1" stop-color="#6e7781"/></linearGradient>
  <radialGradient id="hub" cx=".38" cy=".35"><stop offset="0" stop-color="#454d57"/>
  <stop offset="1" stop-color="#121519"/></radialGradient>
  <linearGradient id="carbon" x1="0" x2="1"><stop offset="0" stop-color="#2d333b"/>
  <stop offset="1" stop-color="#16191d"/></linearGradient>"""


def joint(w):
    r = w * 0.7 + 3
    return (f'<circle r="{r:.1f}" fill="url(#hub)" stroke="#6e7681" stroke-width="1.2"/>'
            f'<circle r="{r * 0.55:.1f}" fill="none" stroke="{ACC}" stroke-width="1" opacity="0.85"/>'
            f'<circle r="1.8" fill="{ACC}"/>')


def link(l, w):
    return (f'<rect x="-{w / 2}" y="-{l}" width="{w}" height="{l}" rx="{w / 2}" fill="url(#shell)" '
            f'stroke="{EDGE_D}" stroke-width="1"/>'
            f'<rect x="-{w / 2}" y="-{l * 0.5 + 2:.1f}" width="{w}" height="4" fill="url(#carbon)" opacity="0.8"/>')


def chain(lengths, widths, series, dur, tip="", jframe=True):
    """Nested serial chain; each segment rotates by its own series."""
    out = tip
    for l, w, s in reversed(list(zip(lengths, widths, series))):
        j = joint(w) + (frame(w * 0.7 + 14, 0.7) if jframe else "")
        out = f'<g>{rot(s, dur)}{link(l, w)}{j}<g transform="translate(0,-{l})">{out}</g></g>'
    return out


def finger(lengths, widths, series, dur, inner=-1, shade="shell"):
    """Shelled phalanges with carbon contact pads on the grasping side and a tactile tip sensor."""
    out = f'<circle cx="{inner * widths[-1] * 0.22:.1f}" cy="-{widths[-1] * 0.1:.1f}" r="1.7" fill="{ACC}"/>'
    for l, w, s in reversed(list(zip(lengths, widths, series))):
        ext = w * 0.4
        pw = w * 0.36
        px = -w / 2 if inner < 0 else w / 2 - pw
        out = (f'<g>{rot(s, dur)}'
               f'<rect x="-{w / 2}" y="-{l + ext:.1f}" width="{w}" height="{l + ext:.1f}" rx="{w / 2}" '
               f'fill="url(#{shade})" stroke="{EDGE_D}" stroke-width="0.9"/>'
               f'<rect x="{px:.1f}" y="-{l - 1:.1f}" width="{pw:.1f}" height="{l - 3:.1f}" rx="{pw / 2:.1f}" fill="url(#carbon)"/>'
               f'<circle r="{w * 0.4:.1f}" fill="url(#hub)" stroke="#6e7681" stroke-width="0.8"/>'
               f'<g transform="translate(0,-{l})">{out}</g></g>')
    return out


def dots(W, H):
    return "".join(f'<circle cx="{x}" cy="{y}" r="0.9" fill="{DIM}"/>'
                   for x in range(20, W, 30) for y in range(20, H, 30))


# ---------- header ----------
# side-view anthropomorphic hand: index/middle/ring/little stacked in depth, opposing 3-segment thumb
PALM = 42                      # wrist cuff + palm, along the approach axis
FINGERS = {  # name: (base x, base y, phalanx lengths, depth index)
    "little": (17, -PALM, [20, 13, 11], 3),
    "ring":   (17, -PALM, [25, 16, 13], 2),
    "middle": (17, -PALM, [27, 18, 14], 1),
    "index":  (17, -PALM, [25, 16, 13], 0),
}
F_W, T_W = [9, 8, 7], [11, 10, 8.5]
THUMB = (-22, -22, [19, 16, 14])
F_CURL, T_CURL = [0.55, 1.0, 0.8], [0.6, 0.9, 0.7]


def fbase(name):
    bx, by, ls, k = FINGERS[name]
    return bx - 2 * k, by - k, ls


def tip(bx, by, ls, angs):
    phi, x, y = 0.0, bx, by
    for l, a in zip(ls, angs):
        phi += math.radians(a)
        x += l * math.sin(phi)
        y -= l * math.cos(phi)
    return x, y


def fangs(a):
    return [a * c for c in F_CURL]


def tangs(a):
    return [a * c for c in T_CURL]


def solve_finger(name, tx):
    bx, by, ls = fbase(name)
    a = 20.0
    while a > -95 and tip(bx, by, ls, fangs(a))[0] > tx:
        a -= 0.25
    return a


def solve_thumb(tx):
    bx, by, ls = THUMB
    a = -20.0
    while a < 95 and tip(bx, by, ls, tangs(a))[0] < tx:
        a += 0.25
    return a


def header():
    set_samples(360)
    W, H, T = 1200, 380, 27
    TABLE = 330
    BASE = (780, TABLE)
    SHOULDER = (BASE[0], BASE[1] - 14)   # first joint sits on the pedestal
    L1, L2, L3 = 195, 170, 30
    home = (860, 128)

    # --- objects + grasp taxonomy (closed-hand curl per digit, solved for fingertip contact) ---
    objs = []
    # power: cylinder, all digits wrap in front of the can
    cx, CR, CHt = 870, 20, 66
    a = {n: solve_finger(n, -6) for n in FINGERS}
    a["thumb"] = solve_thumb(6)
    objs.append(dict(kind="can", x=cx, top=TABLE - CHt, h=CHt, w=2 * CR, label="POWER", close=a,
                     ee=(cx, TABLE - CHt - 3 - PALM), center=(cx, TABLE - CHt / 2)))
    # tripod: sphere, thumb + index + middle tips at the equator, ring/little tucked
    sx, R = 975, 15
    a = {"index": solve_finger("index", R * 0.8 + F_W[-1] / 2), "middle": solve_finger("middle", R * 0.8 + F_W[-1] / 2),
         "ring": -32, "little": -36, "thumb": solve_thumb(-R * 0.8 - T_W[-1] / 2)}
    d = -tip(*fbase("index"), fangs(a["index"]))[1]
    objs.append(dict(kind="sphere", x=sx, top=TABLE - 2 * R, h=2 * R, w=2 * R, r=R, label="TRIPOD", close=a,
                     ee=(sx, TABLE - R - 1 - d), center=(sx, TABLE - R)))
    # pinch: small cube, index + thumb pads, other fingers curled away
    px, S = 1075, 16
    a = {"index": solve_finger("index", S / 2 + F_W[-1] / 2), "middle": -42, "ring": -46, "little": -48,
         "thumb": solve_thumb(-S / 2 - T_W[-1] / 2)}
    d = -tip(*fbase("index"), fangs(a["index"]))[1]
    objs.append(dict(kind="cube", x=px, top=TABLE - S, h=S, w=S, label="PINCH", close=a,
                     ee=(px, TABLE - S / 2 - d), center=(px, TABLE - S / 2)))

    digits = list(FINGERS) + ["thumb"]
    neutral = {n: 6 for n in FINGERS}
    neutral["thumb"] = -10

    def preshape(o):
        p = {n: o["close"][n] + 28 for n in FINGERS}
        p["thumb"] = o["close"]["thumb"] - 30
        return p

    def mix(p, q, s):
        return {n: p[n] + (q[n] - p[n]) * s for n in digits}

    # --- timeline: three pick-and-place cycles ---
    def state(u):
        k = min(int(u * 3), 2)
        s = u * 3 - k
        o = objs[k]
        g = o["ee"]
        pre, lift = (g[0], g[1] - 50), (g[0], g[1] - 64)
        segs = [(0.00, 0.15, home, home), (0.15, 0.36, home, pre), (0.36, 0.44, pre, g),
                (0.44, 0.52, g, g), (0.52, 0.64, g, lift), (0.64, 0.70, lift, lift),
                (0.70, 0.80, lift, g), (0.80, 0.86, g, g), (0.86, 0.92, g, pre), (0.92, 1.01, pre, home)]
        e = home
        for a0, b0, p, q in segs:
            if s < b0:
                e = lerp(p, q, smooth(a0, b0, s))
                break
        ps = preshape(o)
        hand = mix(neutral, ps, smooth(0.15, 0.36, s))
        hand = mix(hand, o["close"], smooth(0.44, 0.52, s) * (1 - smooth(0.80, 0.86, s)))
        hand = mix(hand, neutral, smooth(0.92, 1.0, s))
        held = 0.52 <= s <= 0.80
        return k, s, e, hand, held

    S_ = [state(u) for u in ts]
    EE = [x[2] for x in S_]

    def elbow_y(sign):
        q1, _ = ik2(SHOULDER, (objs[1]["ee"][0], objs[1]["ee"][1] - L3), L1, L2, sign)
        return SHOULDER[1] - L1 * math.cos(q1)
    sign = min((1, -1), key=elbow_y)
    Q1, Q2, Q3 = [], [], []
    for e in EE:
        wr = (e[0], e[1] - L3)
        assert math.dist(wr, SHOULDER) < L1 + L2 - 4, ("unreachable", e)
        q1, q2 = ik2(SHOULDER, wr, L1, L2, sign)
        Q1.append(math.degrees(q1))
        Q2.append(math.degrees(q2))
        Q3.append(180 - math.degrees(q1) - math.degrees(q2))
    Q1, Q2, Q3 = unwrap(Q1), unwrap(Q2), unwrap(Q3)

    # --- hand ---
    fingers_svg = ""
    for n in ["little", "ring", "middle", "index"]:
        bx, by, ls = fbase(n)
        k = FINGERS[n][3]
        series = [[x[3][n] * c for x in S_] for c in F_CURL]
        fingers_svg += (f'<g transform="translate({bx},{by})">'
                        f'{finger(ls, F_W, series, T, inner=-1, shade="shell" if k == 0 else "shellD")}</g>')
    tb = THUMB
    tser = [[x[3]["thumb"] * c for x in S_] for c in T_CURL]
    thumb_svg = f'<g transform="translate({tb[0]},{tb[1]})">{finger(tb[2], T_W, tser, T, inner=1)}</g>'
    hand = (f'<rect x="-15" y="-12" width="30" height="13" rx="3" fill="url(#carbon)" stroke="{EDGE_D}"/>'
            f'<line x1="-11" y1="-6" x2="11" y2="-6" stroke="{ACC}" stroke-width="1.6" opacity="0.9"/>'
            f'<rect x="-26" y="-{PALM - 2}" width="52" height="{PALM - 12}" rx="10" fill="url(#shell)" stroke="{EDGE_D}" stroke-width="1.2"/>'
            f'<rect x="-24" y="-{PALM - 2}" width="48" height="7" rx="3.5" fill="url(#carbon)"/>'
            f'<path d="M-14,-{PALM - 12} V-16 M8,-{PALM - 12} V-16" stroke="#8c959f" stroke-width="0.8"/>'
            f'<circle cx="18" cy="-19" r="2" fill="{ACC}"/>'
            f'{fingers_svg}{thumb_svg}')
    # mirror so the thumb faces the arm (objects are symmetric, so contacts are unchanged)
    arm = chain([L1, L2, L3], [22, 17, 13], [Q1, Q2, Q3], T, tip=f'<g transform="scale(-1,1)">{hand}</g>')

    # --- objects: geometry, point cloud, 6D pose, bbox, scan ---
    rnd = random.Random(7)
    obj_svg = ""
    for k, o in enumerate(objs):
        x0, top, h, w = o["x"], o["top"], o["h"], o["w"]
        cxo, cyo = o["center"]
        pts = []
        if o["kind"] == "can":
            r = w / 2
            geo = (f'<path d="M{x0 - r},{top} V{TABLE} A{r},4 0 0 0 {x0 + r},{TABLE} V{top}" fill="none" stroke="{DIM}" stroke-width="1.4"/>'
                   f'<ellipse cx="{x0}" cy="{top}" rx="{r}" ry="4" fill="none" stroke="{DIM}" stroke-width="1.4"/>')
            for _ in range(160):
                t_ = rnd.uniform(-math.pi / 2, math.pi / 2)
                pts.append((x0 + r * math.sin(t_), rnd.uniform(top, TABLE) + 4 * math.cos(t_), 0.35 + 0.65 * math.cos(t_)))
            for _ in range(40):
                t_, rr = rnd.uniform(0, 2 * math.pi), r * math.sqrt(rnd.random())
                pts.append((x0 + rr * math.cos(t_), top + 4 * rr / r * math.sin(t_), 0.9))
        elif o["kind"] == "sphere":
            r = o["r"]
            geo = f'<circle cx="{cxo}" cy="{cyo}" r="{r}" fill="none" stroke="{DIM}" stroke-width="1.4"/>'
            for _ in range(110):
                t_, rr = rnd.uniform(0, 2 * math.pi), r * math.sqrt(rnd.random())
                z = math.sqrt(max(0.0, 1 - (rr / r) ** 2))
                pts.append((cxo + rr * math.cos(t_), cyo + rr * math.sin(t_), 0.3 + 0.7 * z))
        else:
            s2 = w / 2
            geo = (f'<rect x="{x0 - s2}" y="{top}" width="{w}" height="{h}" fill="none" stroke="{DIM}" stroke-width="1.4"/>'
                   f'<path d="M{x0 - s2},{top} l5,-5 h{w} v{h} l-5,5 M{x0 + s2},{top} l5,-5" fill="none" stroke="{DIM}" stroke-width="1.4"/>')
            for _ in range(70):
                pts.append((rnd.uniform(x0 - s2, x0 + s2), rnd.uniform(top, TABLE), 0.9))
            for _ in range(25):
                f = rnd.random()
                pts.append((x0 + s2 + 5 * f, rnd.uniform(top, TABLE) - 5 * f, 0.5))
        cloud = "".join(f'<circle cx="{px_:.1f}" cy="{py_:.1f}" r="1.05" fill="{ACC}" opacity="{op_:.2f}"/>'
                        for px_, py_, op_ in pts)

        def in_cycle(fn):
            return [fn(x[1]) if x[0] == k else 0.0 for x in S_]
        cloud_op = [0.12 + v for v in in_cycle(lambda s: 0.88 * smooth(0.02, 0.13, s) * (1 - smooth(0.90, 0.98, s)))]
        pose_op = in_cycle(lambda s: smooth(0.12, 0.16, s) * (1 - smooth(0.88, 0.95, s)))
        scan_op = in_cycle(lambda s: 1.0 if 0.02 < s < 0.13 else 0.0)
        scan_y = [top - 10 + (h + 20) * (smooth(0.02, 0.13, x[1]) if x[0] == k else 0) for x in S_]
        lab_op = in_cycle(lambda s: 1.0)

        bw, bh = w + 12, h + 12
        bx_, by_ = x0 - bw / 2, top - 6
        bb = (f'M{bx_},{by_} h{bw} v{bh} h-{bw} Z M{bx_},{by_} l8,-7 h{bw} l-8,7 '
              f'M{bx_ + bw},{by_} l8,-7 v{bh} l-8,7')
        ax = 14 + h * 0.12
        pose = (f'<g opacity="0">{attr("opacity", pose_op, T)}'
                f'<path d="{bb}" fill="none" stroke="{ACC}" stroke-width="0.8" stroke-dasharray="3 3" opacity="0.7"/>'
                f'<g transform="translate({cxo},{cyo})">'
                f'<line x2="{ax:.1f}" y2="{ax / 2:.1f}" stroke="{RX}" stroke-width="1.6"/>'
                f'<line y2="-{ax * 1.1:.1f}" stroke="{GY}" stroke-width="1.6"/>'
                f'<line x2="-{ax:.1f}" y2="{ax / 2:.1f}" stroke="{BZ}" stroke-width="1.6"/>'
                f'<circle r="2.3" fill="{FG}"/></g></g>')
        off = [(x[2][0] - o["ee"][0], x[2][1] - o["ee"][1]) if (x[0] == k and x[4]) else (0, 0) for x in S_]
        obj_svg += (f'<g>{trans(off, T)}{geo}<g>{attr("opacity", cloud_op, T)}{cloud}</g>{pose}</g>'
                    f'<line x1="{x0 - 34}" x2="{x0 + 34}" stroke="{ACC}" stroke-width="1" opacity="0">'
                    f'{attr("y1", scan_y, T, "{:.1f}")}{attr("y2", scan_y, T, "{:.1f}")}{attr("opacity", scan_op, T)}</line>'
                    f'<text x="{x0}" y="{TABLE + 30}" text-anchor="middle" font-family="{MONO}" font-size="11" '
                    f'letter-spacing="2" fill="{MUTED}" opacity="0.45">{o["label"]}</text>'
                    f'<text x="{x0}" y="{TABLE + 30}" text-anchor="middle" font-family="{MONO}" font-size="11" '
                    f'letter-spacing="2" fill="{ACC}" opacity="0">{attr("opacity", lab_op, T)}{o["label"]}</text>')

    cam = (1150, 44)
    frustum = (f'<path d="M{cam[0]},{cam[1]} L{830},{TABLE + 4} M{cam[0]},{cam[1]} L{1100},{TABLE + 4}" '
               f'stroke="{ACC}" stroke-width="0.8" stroke-dasharray="2 5" opacity="0.3"/>'
               f'<g transform="translate({cam[0]},{cam[1]}) rotate(28)"><rect x="-24" y="-8" width="48" height="16" rx="4" '
               f'fill="{BG}" stroke="{FG}" stroke-width="1.5"/>'
               f'<circle cx="-12" r="3.5" fill="none" stroke="{ACC}"/><circle cx="12" r="3.5" fill="none" stroke="{ACC}"/>'
               f'<circle r="1.6" fill="{RX}">{attr("opacity", [1.0 if 0.02 < x[1] < 0.13 else 0.25 for x in S_], T)}</circle></g>')

    path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in EE[::2])
    plan = f'<path d="{path}" fill="none" stroke="{ACC}" stroke-width="1" stroke-dasharray="2 4" opacity="0.25"/>'
    tbl = (f'<line x1="{BASE[0] - 70}" y1="{TABLE}" x2="1160" y2="{TABLE}" stroke="{DIM}" stroke-width="1.4"/>'
           + "".join(f'<line x1="{x}" y1="{TABLE}" x2="{x - 8}" y2="{TABLE + 10}" stroke="{DIM}"/>'
                     for x in range(BASE[0] - 64, 1160, 14)))
    base = (f'<path d="M{BASE[0] - 28},{BASE[1]} L{BASE[0] - 19},{BASE[1] - 14} H{BASE[0] + 19} L{BASE[0] + 28},{BASE[1]} Z" '
            f'fill="url(#carbon)" stroke="#6e7681" stroke-width="1.5"/>')

    CLIPS = ""

    def typed(text, x, y, fs, ls, t_in, t_out, fill, extra=""):
        """Monospace typewriter on the header loop: type, hold, backspace, repeat (survives image caching)."""
        # static text: no typing animation
        return f'<text x="{x}" y="{y}" font-size="{fs}" fill="{fill}" letter-spacing="{ls}" {extra}>{text}</text>'

    NAME = "OMKAR KSHIRSAGAR"
    ROLE = "robotics systems engineer · dexterous manipulation"
    txt = f'''<g font-family="{MONO}">
    {typed(NAME, 64, 84, 34, 5, (0.3, 1.8), (25.7, 26.5), FG, 'font-weight="600"')}
    {typed(ROLE, 66, 116, 16, 1, (2.1, 4.3), (24.6, 25.5), MUTED)}
    <line x1="66" y1="140" x2="130" y2="140" stroke="{ACC}" stroke-width="2"/>
    <g>
    <text x="64" y="194" font-size="26" fill="{FG}" letter-spacing="1">M ẍ + D ẋ + K x = F<tspan font-size="16" dy="5">ext</tspan></text>
    <text x="64" y="234" font-size="18" fill="{MUTED}">w = G(q) f ,  f ∈ F<tspan font-size="12" dy="4">c</tspan></text>
    <text x="64" y="264" font-size="18" fill="{MUTED}"><tspan font-size="12" dy="-7">W</tspan><tspan dy="7">T</tspan><tspan font-size="12" dy="4">O</tspan><tspan dy="-4"> ∈ SE(3)</tspan></text>
    </g></g>'''

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>{DEFS}{CLIPS}</defs>
  {panel(W, H)}
  {dots(W, H)}
  {txt}
  {tbl}{frustum}{plan}{obj_svg}
  <g transform="translate({SHOULDER[0]},{SHOULDER[1]})">{arm}</g>
  {base}
</svg>
'''


# ---------- skills: ROS 2 node graph ----------
# curated lines (one idea per line) so nothing wraps or overflows at README width
SKILLS = {
    "perception": ["FoundationPose · SAM3", "YOLO · Mask R-CNN", "U-Net · segmentation", "6D pose estimation",
                   "RGB-D · point clouds", "depth estimation", "CAD-based perception", "OpenCV",
                   "multi-cam calibration"],
    "grasp_planning": ["dexterous hands", "multi-finger grasping", "grasp generation", "grasp optimization",
                       "grasp taxonomy", "hand preshaping", "Inspire RH56 series", "Tesollo DG5F-M"],
    "motion_planning": ["MoveIt 2 · MoveIt Pro", "MoveIt Task Constructor", "collision avoidance", "task planning",
                        "kinematics · IK", "reachability analysis", "behavior trees"],
    "execution": ["contact-aware control", "force feedback", "recovery strategies", "admittance control",
                  "Cartesian control", "cooperative dual-arm", "haptics · teleoperation", "motor control",
                  "UR5e · UR10e"],
    "simulation": ["NVIDIA Isaac Sim", "PhysX · Gazebo · RViz", "URDF · USD", "digital twins",
                   "sim-to-real validation", "convex decomposition", "SDF collision geometry"],
    "learning": ["reinforcement learning", "imitation learning", "learning from demos", "policy learning",
                 "PyTorch · TensorFlow", "scikit-learn · Gym"],
    # bottom node, one column under each pipeline stage
    "system": [["Zivid M135 Plus II", "RealSense D435i", "ZEISS cameras", "sensor integration"],
               ["Jetson Nano", "Raspberry Pi", "ESP32 · STM32", "Arduino"],
               ["CAN · MQTT", "SPI · I2C · UART", "PCB design · KiCad", "SOLIDWORKS · Inventor"],
               ["Python · C++ · C", "ROS 2 · Docker", "Linux · Git · GitLab", "NumPy · Pandas"]],
}


def skills():
    W = 1000
    X0, GAP = 18, 56
    BW = (W - 2 * X0 - 3 * GAP) / 4
    FS, LH = 12, 20                        # body font size / line height
    PAD = 16                               # inner horizontal padding
    T_BASE, RULE, BODY0, BOT = 27, 40, 62, 20
    cols = [X0 + i * (BW + GAP) for i in range(4)]
    char_w = 0.6 * FS                      # monospace advance

    for v in SKILLS.values():
        for ln in (sum(v, []) if isinstance(v[0], list) else v):
            assert len(ln) * char_w <= BW - 2 * PAD, ("line too long", ln)

    def hbox(n):
        return BODY0 + (n - 1) * LH + BOT

    def shell(name, x, y, w, h):
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{BOX}" stroke="{EDGE}" stroke-width="1.5"/>'
                f'<circle cx="{x + PAD + 3}" cy="{y + T_BASE - 4.5}" r="3.5" fill="{GY}">'
                f'<animate attributeName="opacity" values="1;0.3;1" dur="2s" repeatCount="indefinite"/></circle>'
                f'<text x="{x + PAD + 14}" y="{y + T_BASE}" font-size="14" font-weight="600" fill="{ACC}" '
                f'letter-spacing="0.5">/{name}</text>'
                f'<line x1="{x + PAD}" y1="{y + RULE}" x2="{x + w - PAD}" y2="{y + RULE}" stroke="{EDGE}"/>')

    def body(x, y, lines):
        return "".join(f'<text x="{x + PAD}" y="{y + BODY0 + i * LH}" font-size="{FS}" fill="{FG}" '
                       f'opacity="0.82">{ln}</text>' for i, ln in enumerate(lines))

    top = {"simulation": 1, "learning": 2}
    mid = ["perception", "grasp_planning", "motion_planning", "execution"]
    sysc = SKILLS["system"]

    yA = 18
    hA = max(hbox(len(SKILLS[k])) for k in top)
    yB = yA + hA + 64
    hB = max(hbox(len(SKILLS[k])) for k in mid)
    yC = yB + hB + 64
    hC = hbox(max(len(c) for c in sysc))
    H = yC + hC + 18

    out = []
    for k, c in top.items():
        out.append(shell(k, cols[c], yA, BW, hA) + body(cols[c], yA, SKILLS[k]))
    for i, k in enumerate(mid):
        out.append(shell(k, cols[i], yB, BW, hB) + body(cols[i], yB, SKILLS[k]))
    out.append(shell("system", X0, yC, W - 2 * X0, hC))
    for i, c in enumerate(sysc):
        out.append(body(cols[i], yC, c))
        if i:
            xs = cols[i] - GAP / 2
            out.append(f'<line x1="{xs}" y1="{yC + RULE + 12}" x2="{xs}" y2="{yC + hC - 14}" stroke="{EDGE}" '
                       f'stroke-dasharray="2 4"/>')

    edges = []   # (path, label, lx, ly, anchor)
    ym = yB + 26
    for i, lab in enumerate(["/pose", "/grasp", "/plan"]):
        x1, x2 = cols[i] + BW, cols[i + 1]
        edges.append((f"M{x1 + 2},{ym} L{x2 - 3},{ym}", lab, (x1 + x2) / 2, ym - 9, "middle"))
    for c, lab in ((1, "/digital_twin"), (2, "/policy")):
        x = cols[c] + BW / 2
        edges.append((f"M{x},{yA + hA + 2} L{x},{yB - 3}", lab, x + 10, (yA + hA + yB) / 2 + 4, "start"))
    for c, lab, up in ((0, "/camera/points", True), (3, "/joint_commands", False)):
        x = cols[c] + BW / 2
        a, b = (yC - 2, yB + hB + 3) if up else (yB + hB + 2, yC - 3)
        edges.append((f"M{x},{a} L{x},{b}", lab, x + 10, (yB + hB + yC) / 2 + 4, "start"))

    e_svg = ""
    for i, (d, lab, lx, ly, anc) in enumerate(edges):
        e_svg += (f'<path d="{d}" stroke="{EDGE}" stroke-width="1.5" fill="none" marker-end="url(#ah)"/>'
                  f'<text x="{lx}" y="{ly}" text-anchor="{anc}" font-size="10.5" fill="{MUTED}">{lab}</text>'
                  f'<circle r="3" fill="{ACC}"><animateMotion dur="2.2s" begin="-{i * 0.31:.2f}s" '
                  f'repeatCount="indefinite" path="{d}"/></circle>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H:.0f}" width="{W}" height="{H:.0f}" font-family="{MONO}">
  <defs><marker id="ah" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">
    <path d="M0,0 L8,4 L0,8 Z" fill="{EDGE}"/></marker></defs>
  {panel(W, H)}
  {dots(W, int(H))}
  {e_svg}
  {"".join(out)}
</svg>
'''


# ---------- footer ----------
def footer():
    set_samples(160)
    W, H, T = 1200, 210, 10
    L1, L2, L3 = 92, 80, 20
    BL, BR = (420, 200), (780, 200)
    HALF = 110

    QL, QR, C, TH = [[], [], []], [[], [], []], [], []
    for u in ts:
        w = 2 * math.pi * u
        c = (600 + 46 * math.sin(w), 78 + 16 * math.sin(2 * w + 0.4))
        th = math.radians(9 * math.sin(w + 0.9))
        C.append(c)
        TH.append(math.degrees(th))
        d = (math.cos(th), math.sin(th))
        nup = (math.sin(th), -math.cos(th))
        for Q, s, b, sign in ((QL, -1, BL, 1), (QR, 1, BR, -1)):
            g = (c[0] + s * HALF * d[0], c[1] + s * HALF * d[1])
            wr = (g[0] - L3 * nup[0], g[1] - L3 * nup[1])
            q1, q2 = ik2((b[0], b[1] - 12), wr, L1, L2, sign)
            Q[0].append(math.degrees(q1))
            Q[1].append(math.degrees(q2))
            Q[2].append(math.degrees(th - q1 - q2))
    QL = [unwrap(s) for s in QL]
    QR = [unwrap(s) for s in QR]

    clamp = (f'<rect x="-13" y="-8" width="26" height="8" rx="2" fill="url(#carbon)" stroke="{EDGE_D}"/>'
             f'<rect x="-14" y="-26" width="6" height="19" rx="2" fill="url(#shell)" stroke="{EDGE_D}"/>'
             f'<rect x="8" y="-26" width="6" height="19" rx="2" fill="url(#shell)" stroke="{EDGE_D}"/>')

    def arm(b, Q):
        return (f'<g transform="translate({b[0]},{b[1] - 12})">{chain([L1, L2, L3], [15, 12, 9], Q, T, tip=clamp, jframe=False)}</g>'
                f'<path d="M{b[0] - 24},{b[1]} L{b[0] - 16},{b[1] - 12} H{b[0] + 16} L{b[0] + 24},{b[1]} Z" '
                f'fill="url(#carbon)" stroke="#6e7681" stroke-width="1.5"/>')

    # shared object: rigid bar held between the gripper jaws
    JAW = 16
    sq = [0.5 + 0.5 * math.sin(4 * math.pi * u) for u in ts]
    arrows = ""
    for s in (-1, 1):
        x0 = s * (HALF - 14)
        arrows += (f'<line x1="{x0}" y1="-16" y2="-16" stroke="{ACC}" stroke-width="1.4" opacity="0.8">'
                   f'{attr("x2", [x0 - s * (10 + 18 * v) for v in sq], T, "{:.1f}")}</line>')
    bar = (f'<g>{trans(C, T)}<g>{rot(TH, T)}'
           f'<rect x="-{HALF + 14}" y="-{JAW + 6}" width="{2 * HALF + 28}" height="12" rx="4" fill="{BG}" stroke="{ACC}" stroke-width="1.6"/>'
           f'<g transform="translate(0,-{JAW})">{frame(18, 0.9)}<circle r="2.4" fill="{FG}"/></g>'
           f'<g transform="translate(0,-{JAW})">{arrows}</g></g></g>')
    trace = "M" + " L".join(f"{x:.1f},{y - JAW:.1f}" for x, y in C) + " Z"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>{DEFS}</defs>
  {panel(W, H)}
  {dots(W, H)}
  <line x1="300" y1="{BL[1]}" x2="900" y2="{BL[1]}" stroke="{DIM}" stroke-width="1.4"/>
  <path d="{trace}" fill="none" stroke="{ACC}" stroke-width="1" stroke-dasharray="2 4" opacity="0.35"/>
  {arm(BL, QL)}{arm(BR, QR)}{bar}
</svg>
'''


ISAAC = '''<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 256 256">
  <rect width="256" height="256" rx="60" fill="#242938"/>
  <g transform="translate(48,48) scale(6.667)" fill="#76B900"><path d="M8.948 8.798v-1.43a6.7 6.7 0 0 1 .424-.018c3.922-.124 6.493 3.374 6.493 3.374s-2.774 3.851-5.75 3.851c-.398 0-.787-.062-1.158-.185v-4.346c1.528.185 1.837.857 2.747 2.385l2.04-1.714s-1.492-1.952-4-1.952a6.016 6.016 0 0 0-.796.035m0-4.735v2.138l.424-.027c5.45-.185 9.01 4.470 9.010 4.470s-4.08 4.964-8.33 4.964c-.37 0-.733-.035-1.095-.097v1.325c.3.035.61.062.91.062 3.957 0 6.82-2.023 9.593-4.408.459.371 2.34 1.263 2.730 1.652-2.633 2.208-8.772 3.984-12.253 3.984-.335 0-.653-.018-.971-.053v1.864H24V4.063zm0 10.326v1.131c-3.657-.654-4.673-4.460-4.673-4.460s1.758-1.944 4.673-2.262v1.237H8.94c-1.528-.186-2.73 1.245-2.73 1.245s.68 2.412 2.739 3.110M2.456 10.9s2.164-3.197 6.5-3.533V6.201C4.153 6.59 0 10.653 0 10.653s2.35 6.802 8.948 7.420v-1.237c-4.840-.6-6.492-5.936-6.492-5.936z"/></g>
</svg>
'''

os.makedirs("assets", exist_ok=True)
for theme, suffix in (("dark", ""), ("light", "-light")):
    set_theme(theme)
    open(f"assets/header{suffix}.svg", "w").write(header())
    open(f"assets/skills{suffix}.svg", "w").write(skills())
    open(f"assets/footer{suffix}.svg", "w").write(footer())
open("assets/isaac.svg", "w").write(ISAAC)
open("assets/isaac-light.svg", "w").write(ISAAC.replace("#242938", "#F4F2ED"))
