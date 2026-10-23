"""Algorithm scenes: WFA classifier, policy trees, PMP controller, scuffedQuant, NVMe storage tier."""
from __future__ import annotations

import numpy as np
from manim import *  # noqa: F401,F403

from style import (BAD, BG, COLD, EDGE, GOLD, HOT, MUTED, OK, PANEL, SPILL, TEXT, TC, Captioned, T, arrow, box,
                   packet)

STATE_COL = {"cold": COLD, "warm": GOLD, "hot": HOT}


def M(tex: str, size: float = 30, color: str = TEXT) -> MathTex:
    return MathTex(tex, font_size=size, color=color)


# --------------------------------------------------------------------------------------------- 08
class S08WFA(Captioned):
    tag = "8 · WFA classifier: static thresholds vs learned weights"

    def construct(self):
        pos = {"cold": LEFT * 5.2 + UP * 0.2, "warm": LEFT * 3.3 + UP * 1.95, "hot": LEFT * 1.4 + UP * 0.2}
        nodes = {}
        for s, p in pos.items():
            c = Circle(0.62, color=STATE_COL[s], stroke_width=3, fill_color=BG, fill_opacity=1).move_to(p)
            nodes[s] = VGroup(c, T(s.upper(), 18, STATE_COL[s], weight="BOLD").move_to(p))
        edges = VGroup()
        for a, b in [("cold", "warm"), ("warm", "hot"), ("hot", "cold")]:
            edges.add(CurvedArrow(nodes[a].get_center(), nodes[b].get_center(), angle=-0.5, color=EDGE,
                                  stroke_width=2.5, tip_length=0.16).scale(0.62, about_point=(pos[a] + pos[b]) / 2))
            edges.add(CurvedArrow(nodes[b].get_center(), nodes[a].get_center(), angle=-0.5, color=EDGE,
                                  stroke_width=2.5, tip_length=0.16).scale(0.62, about_point=(pos[a] + pos[b]) / 2))
        self.play(LaggedStart(*[GrowFromCenter(n) for n in nodes.values()], lag_ratio=0.2), Create(edges), run_time=1.4)
        self.caption("One three-state automaton per tensor. The state decides the endpoint: hot → HOT, warm/cold → COLD.")

        feats = ["log2 size", "access freq", "queue depth", "is_prefill", "is_decode", "log2 seq len",
                 "log2 inter-arrival", "is_control"]
        fx = VGroup(*[T(f, 15, TEXT, mono=True) for f in feats]).arrange(DOWN, buff=0.07, aligned_edge=LEFT)
        fbox = SurroundingRectangle(fx, color=EDGE, buff=0.18, corner_radius=0.1)
        ft = T("SignalVector.features()", 16, MUTED).next_to(fbox, UP, buff=0.08)
        fg = VGroup(fx, fbox, ft).move_to(RIGHT * 0.75 + UP * 0.85)
        self.play(FadeIn(fg, shift=LEFT * 0.2))
        eq = M(r"P(s' \mid s, x) = \operatorname{softmax}_{s'}\big(W[s,s'] \cdot \varphi(x)\big)", 32).move_to(RIGHT * 4.25 + UP * 2.2)
        eq.scale_to_fit_width(min(eq.width, 4.6)).next_to(fbox, RIGHT, buff=0.3).align_to(fbox, UP)
        phi = VGroup(T("φ(x) = standardized features", 15, MUTED), T("+ bias", 15, MUTED),
                     T("+ log2 size × is_prefill", 15, HOT), T("+ log2 size × is_decode", 15, HOT)
                     ).arrange(DOWN, buff=0.06, aligned_edge=LEFT).next_to(eq, DOWN, buff=0.3).align_to(eq, LEFT)
        fit = T("W: 3×3×F, Adam on cross-entropy + L2", 15, MUTED).next_to(phi, DOWN, buff=0.25).align_to(phi, LEFT)
        self.play(Write(eq), run_time=1.2)
        self.play(FadeIn(phi), FadeIn(fit))
        self.caption("The learned WFA scores every next state from the signal vector. The two interaction terms let each phase keep its own size cutoff.", 1.0)

        # walk a few transfers through the automaton
        cur = ["cold"]

        def go(s):
            self.play(nodes[cur[0]][0].animate.set_fill(BG, 1), nodes[s][0].animate.set_fill(STATE_COL[s], 0.35), run_time=0.35)
            cur[0] = s

        ex = [("32 B · token · decode", "hot"), ("64 KiB · KV · decode", "hot"), ("4 MiB · KV · prefill", "cold"),
              ("48 KiB · KV · prefill", "warm")]
        tag = None
        for txt, s in ex:
            t = T(txt, 17, STATE_COL[s], mono=True).move_to(LEFT * 3.3 + DOWN * 1.3)
            self.play(FadeIn(t, shift=UP * 0.15), FadeOut(tag) if tag else Wait(0.01), run_time=0.35)
            go(s)
            self.wait(0.5)
            tag = t
        self.play(FadeOut(tag), *[FadeOut(m) for m in (fg, phi, fit)], eq.animate.scale(0.75).to_corner(UR, buff=0.35))

        # number line: static vs learned cutoffs
        axis = NumberLine(x_range=[5, 26, 1], length=10.2, color=EDGE, include_ticks=False).move_to(RIGHT * 0.95 + DOWN * 1.45)
        labs = {5: "32 B", 12: "4 KiB", 16: "64 KiB", 18: "256 KiB", 22: "4 MiB", 26: "64 MiB"}
        lab_g = VGroup(*[T(v, 13, MUTED).next_to(axis.n2p(k), DOWN, buff=0.12) for k, v in labs.items()])
        ticks = VGroup(*[Line(axis.n2p(k) + UP * 0.08, axis.n2p(k) + DOWN * 0.08, color=EDGE) for k in labs])
        Y_ST, Y_LD, Y_LP = 1.15, 0.0, -0.75

        def band(y, a, b, col, text):
            r = Rectangle(width=axis.n2p(b)[0] - axis.n2p(a)[0], height=0.42, stroke_width=0, fill_color=col,
                          fill_opacity=0.35).move_to([(axis.n2p(a)[0] + axis.n2p(b)[0]) / 2, y, 0])
            t = T(text, 13, TEXT).move_to(r)
            return VGroup(r, t)

        self.play(*[FadeOut(m) for m in list(nodes.values()) + [edges]], Create(axis), FadeIn(lab_g, ticks))
        st = VGroup(band(Y_ST, 5, 12, HOT, "hot"), band(Y_ST, 12, 18, GOLD, "access count decides"),
                    band(Y_ST, 18, 26, COLD, "cold"))
        stl = T("static", 15, MUTED).next_to(st, LEFT, buff=0.15)
        self.play(FadeIn(st), FadeIn(stl))
        self.caption("Static WFAClassifier: under 4 KiB hot, over 256 KiB cold, in between by access count.")
        dots = VGroup()
        rng = np.random.default_rng(3)
        for k in range(14):
            v = rng.uniform(12.1, 17.9)
            dots.add(Dot([axis.n2p(v)[0], Y_ST + 0.4, 0], radius=0.07, color=HOT))
        dl = T("decode KV deltas", 13, HOT).next_to(dots, UP, buff=0.08)
        self.play(LaggedStart(*[FadeIn(d, scale=0.5) for d in dots], lag_ratio=0.05), FadeIn(dl))
        self.caption("Decode KV deltas (4 KiB to 256 KiB) land in the middle band; most have not been seen often enough yet, so they go cold.")
        self.play(*[d.animate.set_color(COLD) for i, d in enumerate(dots) if i % 6], run_time=0.8)
        self.wait(1.0)

        ld = VGroup(band(Y_LD, 5, 18, HOT, "hot  (decode)"), band(Y_LD, 18, 26, GOLD, "warm"))
        lp = VGroup(band(Y_LP, 5, 16, GOLD, "warm  (prefill)"), band(Y_LP, 16, 26, COLD, "cold"))
        ldl = T("learned", 15, MUTED).next_to(VGroup(ld, lp), LEFT, buff=0.15)
        self.play(FadeIn(ld), FadeIn(lp), FadeIn(ldl))
        moved = dots.copy()
        self.play(*[m.animate.move_to([m.get_center()[0], Y_LD + 0.4, 0]).set_color(HOT) for m in moved], run_time=0.9)
        self.caption("The learned weights recover a per-phase cutoff: decode deltas stay hot, prefill bulk goes cold.", 1.2)
        self.caption("Synthetic traces, and partly by construction (the labels define decode deltas as hot). Real telemetry is the test.", 2.2)


# --------------------------------------------------------------------------------------------- 09
class S09Policy(Captioned):
    tag = "9 · Rule-Node Expression Trees"

    def construct(self):
        rules = [
            (100, "control-messages-hot", "role ∈ {metadata, token}", "route=hot · final"),
            (90, "spill-bulk-under-gpu-pressure", "gpu ≥ 0.9 ∧ size > 256K ∧ ¬decode", "route=spill"),
            (80, "decode-small-kv-hot", "decode ∧ kv ∧ size ≤ 256K", "route=hot"),
            (70, "prefill-bulk-cold", "prefill ∧ size > 64K", "route=cold"),
            (60, "compress-bulk-when-link-busy", "link ≥ 0.8 ∧ route ∈ {cold, spill} ∧ size ≥ 256K", "compress=true"),
            (30, "wfa-hot", "wfa = hot ∧ size ≤ 256K", "route=hot"),
            (20, "tiny-anything-hot", "size < 4K", "route=hot"),
        ]
        cards = VGroup()
        for pr, name, cond, then in rules:
            bg = RoundedRectangle(width=6.0, height=0.62, corner_radius=0.08, stroke_color=EDGE, stroke_width=1.5,
                                  fill_color=PANEL, fill_opacity=1)
            p = T(str(pr), 15, MUTED, mono=True).move_to(bg.get_left() + RIGHT * 0.3)
            n = T(name, 15, TEXT, weight="BOLD").move_to(bg.get_left() + RIGHT * 0.62 + UP * 0.13, aligned_edge=LEFT)
            c = T(cond, 12, MUTED, mono=True).move_to(bg.get_left() + RIGHT * 0.62 + DOWN * 0.15, aligned_edge=LEFT)
            th = T(then, 13, OK).move_to(bg.get_right() + LEFT * 0.12, aligned_edge=RIGHT).shift(UP * 0.13)
            cards.add(VGroup(bg, p, n, c, th))
        cards.arrange(DOWN, buff=0.08).move_to(LEFT * 3.65 + UP * 0.05)
        dflt = T("default: route=cold, compress=false", 14, MUTED).next_to(cards, DOWN, buff=0.1).align_to(cards, LEFT)
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.15) for c in cards], lag_ratio=0.07), FadeIn(dflt), run_time=1.4)
        self.caption("Rules are boolean trees over signals and context, tried in priority order (default_policy.json).")

        inp = VGroup(T("transfer", 16, MUTED, weight="BOLD"), T("role=kv  phase=prefill", 15, TEXT, mono=True),
                     T("size=4 MiB", 15, TEXT, mono=True), T("context", 16, MUTED, weight="BOLD"),
                     T("gpu_mem_util=0.93", 15, TEXT, mono=True), T("link_util=0.85", 15, TEXT, mono=True)
                     ).arrange(DOWN, buff=0.07, aligned_edge=LEFT)
        ib = SurroundingRectangle(inp, color=EDGE, buff=0.15, corner_radius=0.1)
        ig = VGroup(inp, ib).move_to(RIGHT * 2.3 + UP * 1.95)
        dec_route = ValueTracker(0)
        dl = VGroup(T("decision", 16, MUTED, weight="BOLD"), T("route    -", 16, TEXT, mono=True),
                    T("compress -", 16, TEXT, mono=True)).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
        db = RoundedRectangle(width=2.25, height=dl.height + 0.3, corner_radius=0.1, stroke_color=OK, stroke_width=2)
        dl.move_to(db).align_to(db, LEFT).shift(RIGHT * 0.15)
        dg = VGroup(dl, db).next_to(ig, RIGHT, buff=0.3).align_to(ig, UP)
        self.play(FadeIn(ig), FadeIn(dg))

        def mark(i, ok, why=None):
            col = OK if ok else BAD
            sym = T("✓" if ok else "✗", 20, col, weight="BOLD").next_to(cards[i], RIGHT, buff=0.1)
            anims = [cards[i][0].animate.set_stroke(col, 2.5), FadeIn(sym)]
            out = [sym]
            if why:
                w = T(why, 13, MUTED).next_to(sym, RIGHT, buff=0.08)
                anims.append(FadeIn(w))
                out.append(w)
            self.play(*anims, run_time=0.4)
            self.wait(0.6)
            return out

        # rule 100
        mark(0, False, "role is kv")
        # rule 90 as a tree
        self.caption("Rule 90 as its tree: an AND over two thresholds and a NOT. Each leaf reads a signal or context field.")
        root = box(1.0, 0.5, color=EDGE, fill=BG, label="AND", size=16).move_to(RIGHT * 2.9 + DOWN * 0.3)
        l1 = box(2.05, 0.5, color=EDGE, fill=BG, label="gpu_mem_util ≥ 0.9", size=13)
        l2 = box(1.75, 0.5, color=EDGE, fill=BG, label="size > 256 KiB", size=13)
        nt = box(0.9, 0.5, color=EDGE, fill=BG, label="NOT", size=15)
        VGroup(l1, l2, nt).arrange(RIGHT, buff=0.3).next_to(root, DOWN, buff=0.55)
        l3 = box(2.05, 0.5, color=EDGE, fill=BG, label="phase ∈ {decode}", size=13).next_to(nt, DOWN, buff=0.45)
        es = VGroup(*[Line(root.get_bottom(), x.get_top(), color=EDGE, stroke_width=2) for x in (l1, l2, nt)],
                    Line(nt.get_bottom(), l3.get_top(), color=EDGE, stroke_width=2))
        tree = VGroup(root, l1, l2, nt, l3, es)
        self.play(FadeIn(tree), cards[1][0].animate.set_stroke(GOLD, 2.5))
        for leaf, ok in [(l1, True), (l2, True), (l3, False)]:
            self.play(leaf[0].animate.set_stroke(OK if ok else BAD, 3), run_time=0.35)
        self.play(nt[0].animate.set_stroke(OK, 3), run_time=0.35)
        self.play(root[0].animate.set_stroke(OK, 3), run_time=0.35)
        mark(1, True)
        new_r = T("route    spill", 16, SPILL, mono=True).move_to(dl[1], aligned_edge=LEFT)
        self.play(Transform(dl[1], new_r))
        self.caption("A matching rule fills only decision fields that are still unset. Route now belongs to rule 90.", 0.6)
        self.play(FadeOut(tree))
        mark(2, False, "short-circuit: not decode")
        mark(3, True, "route already set")
        self.caption("Rule 60 reads the route decided so far, so compression follows the spill.")
        mark(4, True)
        new_c = T("compress true", 16, OK, mono=True).move_to(dl[2], aligned_edge=LEFT)
        self.play(Transform(dl[2], new_c))
        mark(5, False, "wfa: cold")
        mark(6, False, "size ≥ 4K")
        self.caption("Result: spill to NVMe and compress, with a trace of which rule set each field and why.", 2.4)


# --------------------------------------------------------------------------------------------- 10
class S10PMP(Captioned):
    tag = "10 · PMP bang-bang controller with a storage arm"

    def construct(self):
        two = VGroup(
            T("two arms (Update 4)", 17, MUTED, weight="BOLD"),
            M(r"S = \lambda_{q_H} C \mu_H - \lambda_{q_C} C \mu_C", 30),
            T("S > 0: hot congested → cold      S < 0 → hot", 15, TEXT),
        ).arrange(DOWN, buff=0.18, aligned_edge=LEFT).move_to(LEFT * 3.6 + UP * 2.0)
        self.play(FadeIn(two[0]), Write(two[1]), FadeIn(two[2]), run_time=1.4)
        self.caption("Pontryagin's maximum principle: the Hamiltonian is linear in the control, so the optimum is bang-bang.")
        three = VGroup(
            T("three arms (Update 6): pick the smallest", 17, MUTED, weight="BOLD"),
            M(r"\sigma_H = \alpha\, q_H\, C\, \mu_H", 30, HOT),
            M(r"\sigma_C = \beta\, q_C\, C\, \mu_C", 30, COLD),
            M(r"\sigma_S = \delta\, q_S\, \mu_S - \gamma\, p", 30, SPILL),
            M(r"p = \frac{\max(0,\ u - u_0)}{1 - u_0}", 28, TEXT),
        ).arrange(DOWN, buff=0.16, aligned_edge=LEFT).next_to(two, DOWN, buff=0.4).align_to(two, LEFT)
        self.play(FadeIn(three[0]), LaggedStart(*[Write(m) for m in three[1:]], lag_ratio=0.25), run_time=2.0)
        self.caption("Shadow prices are approximated by queue depth. GPU occupancy u above the watermark u0 makes spilling cheap.", 1.0)

        # bars
        base_y = 0.1
        xs = {"H": 2.2, "C": 3.6, "S": 5.0}
        cols = {"H": HOT, "C": COLD, "S": SPILL}
        base = Line(RIGHT * 1.4 + UP * base_y, RIGHT * 5.8 + UP * base_y, color=EDGE, stroke_width=2)
        blabs = VGroup(*[M(r"\sigma_" + k, 26, cols[k]).move_to(RIGHT * x + UP * (base_y - 1.75)) for k, x in xs.items()])
        gauge = Rectangle(width=0.3, height=2.4, stroke_color=EDGE, stroke_width=1.5).move_to(RIGHT * 6.55 + UP * 0.9)
        wm = DashedLine(gauge.get_left() + LEFT * 0.12 + UP * (2.4 * 0.85 - 1.2), gauge.get_right() + RIGHT * 0.12 + UP * (2.4 * 0.85 - 1.2),
                        color=BAD, stroke_width=2)
        gl = TC("GPU\nu", 13, MUTED).next_to(gauge, DOWN, buff=0.08)
        wl = M("u_0", 22, BAD).next_to(wm, LEFT, buff=0.05)
        self.play(Create(base), FadeIn(blabs), FadeIn(gauge, wm, gl, wl))

        qH = [2, 3, 5, 6, 4, 2, 1, 1, 2, 2, 1, 1]
        qC = [6, 5, 3, 2, 2, 3, 6, 8, 9, 9, 8, 7]
        qS = [0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 3]
        us = [.50, .55, .60, .65, .70, .75, .82, .88, .93, .95, .90, .86]
        u0, gamma, delta = 0.85, 14.0, 0.6
        unit = 0.22

        def bars(t):
            p = max(0.0, us[t] - u0) / (1 - u0)
            sig = {"H": 1.0 * qH[t], "C": 0.8 * qC[t]}
            if p > 0:
                sig["S"] = delta * qS[t] - gamma * p
            best = min(sig, key=sig.get)
            g = VGroup()
            for k, x in xs.items():
                if k not in sig:
                    g.add(T("off", 14, MUTED).move_to(RIGHT * x + UP * (base_y + 0.25)))
                    continue
                h = max(abs(sig[k]) * unit, 0.02)
                r = Rectangle(width=0.8, height=h, stroke_width=3 if k == best else 0, stroke_color=TEXT,
                              fill_color=cols[k], fill_opacity=0.95 if k == best else 0.4)
                r.move_to(RIGHT * x + UP * (base_y + (h / 2 if sig[k] >= 0 else -h / 2)))
                g.add(r)
            fill = Rectangle(width=0.3, height=max(2.4 * us[t], 0.01), stroke_width=0,
                             fill_color=BAD if us[t] > u0 else COLD, fill_opacity=0.85)
            fill.move_to(gauge.get_bottom(), aligned_edge=DOWN)
            g.add(fill)
            return g, best

        strip = VGroup()
        cur, best = bars(0)
        self.play(FadeIn(cur))
        for t in range(12):
            new, best = bars(t)
            sq = Square(0.36, stroke_width=0, fill_color=cols[best], fill_opacity=0.9)
            sq.move_to(RIGHT * (1.6 + t * 0.4) + DOWN * 2.6)
            lt = T(best, 13, BG, weight="BOLD").move_to(sq)
            self.play(Transform(cur, new), FadeIn(VGroup(sq, lt)), run_time=0.55)
            strip.add(VGroup(sq, lt))
            if t == 3:
                self.caption("Below the watermark only H and C compete: traffic goes to whichever queue is cheaper.")
            if t == 7:
                self.caption("Past u0 the spill coefficient goes negative and wins: bulk goes to NVMe until pressure drops.")
            self.wait(0.25)
        st = T("decision per step (illustrative values)", 13, MUTED).next_to(strip, UP, buff=0.08).align_to(strip, LEFT)
        self.play(FadeIn(st))
        self.caption("A deadband keeps the last arm while it is within a margin of the best, so decisions don't chatter.", 2.4)


# --------------------------------------------------------------------------------------------- 11
LM3 = np.array([-2.1520, -1.3440, -0.7560, -0.2451, 0.2451, 0.7560, 1.3440, 2.1520])  # Lloyd-Max, N(0,1), 3 bits;
# scuffed_quant fits its codebook to rotated unit-vector coordinates, which times sqrt(d) is close to this


def hadamard(n):
    H = np.array([[1.0]])
    while H.shape[0] < n:
        H = np.block([[H, H], [H, -H]])
    return H


class S11ScuffedQuant(Captioned):
    tag = "11 · scuffedQuant: rotate, quantize, sketch the residual"

    def construct(self):
        d = 16
        x = np.array([0.2, -0.1, 3.1, 0.05, -0.3, 0.15, 0.1, -2.4, 0.2, 0.0, -0.1, 0.3, 0.1, -0.2, 0.25, 0.05])
        xn = x / np.linalg.norm(x)
        signs = np.array([1, -1, 1, 1, -1, 1, -1, -1, 1, 1, -1, 1, -1, 1, 1, -1])
        rot = (hadamard(d) / np.sqrt(d)) @ (signs * xn) * np.sqrt(d)  # ~N(0,1) coordinates
        q = LM3[np.argmin(np.abs(rot[:, None] - LM3[None, :]), axis=1)]
        res = rot - q

        scale = 0.42
        x0 = -5.6
        base = Line(LEFT * 6.2 + DOWN * 0.1, RIGHT * 0.2 + DOWN * 0.1, color=EDGE, stroke_width=1.5)

        def barset(v, col, s=scale):
            g = VGroup()
            for i, val in enumerate(v):
                h = max(abs(val) * s, 0.02)
                r = Rectangle(width=0.3, height=h, stroke_width=0, fill_color=col, fill_opacity=0.9)
                r.move_to([x0 + i * 0.38, -0.1 + (h / 2 if val >= 0 else -h / 2), 0])
                g.add(r)
            return g

        bx = barset(x, COLD)
        lab = T("one K vector, head_dim 64 (16 coords shown)", 15, MUTED).next_to(base, UP, buff=1.55).align_to(base, LEFT)
        self.play(Create(base), FadeIn(lab), LaggedStart(*[GrowFromEdge(b, DOWN) for b in bx], lag_ratio=0.04))
        self.caption("KV vectors have a few large coordinates. Quantizing them directly wastes levels on the outliers.")

        steps = VGroup(*[T(s, 16, MUTED) for s in
                         ["1  normalize, keep ‖x‖", "2  random-sign Hadamard", "3  Lloyd-Max, 3 bits",
                          "4  residual r = x − x̂", "5  QJL: 256 sign bits of S·r"]]).arrange(DOWN, buff=0.17, aligned_edge=LEFT)
        steps.move_to(RIGHT * 3.6 + UP * 1.1)
        self.play(FadeIn(steps))

        def hi(i):
            self.play(*[s.animate.set_color(TEXT if j == i else MUTED) for j, s in enumerate(steps)], run_time=0.3)

        hi(0)
        bn = barset(xn * 4.0, COLD)
        self.play(Transform(bx, bn), run_time=0.8)
        hi(1)
        br = barset(rot, COLD)
        self.play(Transform(bx, br), run_time=1.2)
        self.caption("The rotation spreads energy evenly: coordinates look Gaussian, so one fixed codebook fits every vector.", 1.0)
        hi(2)
        levels = VGroup(*[DashedLine([x0 - 0.3, -0.1 + v * scale, 0], [x0 + 15 * 0.38 + 0.3, -0.1 + v * scale, 0], color=GOLD,
                                     stroke_width=1.5, dash_length=0.06) for v in LM3])
        self.play(Create(levels), run_time=0.8)
        bq = barset(q, GOLD)
        self.play(Transform(bx, bq), run_time=1.0)
        self.caption("Eight Lloyd-Max levels fit to the rotated coordinates; each coordinate becomes a 3-bit index.", 0.8)
        hi(3)
        ghost = barset(rot, COLD).set_opacity(0.25)
        self.add(ghost)
        brs = barset(res, BAD, scale * 1.0)
        self.play(FadeOut(levels), Transform(bx, brs), run_time=1.0)
        self.play(FadeOut(ghost))
        hi(4)
        bits = VGroup(*[Square(0.11, stroke_width=0, fill_color=(OK if b else BAD), fill_opacity=0.9)
                        for b in (np.random.default_rng(7).standard_normal(256) > 0)])
        bits.arrange_in_grid(rows=4, cols=64, buff=0.02).move_to(LEFT * 3.0 + DOWN * 2.15)
        bl = T("sign(S·r): 256 bits", 14, MUTED).next_to(bits, UP, buff=0.06).align_to(bits, LEFT)
        self.play(FadeIn(bl), LaggedStart(*[FadeIn(b) for b in bits], lag_ratio=0.003), run_time=1.2)
        self.caption("A 1-bit Johnson-Lindenstrauss sketch of the residual keeps inner products unbiased (QJL).", 1.0)

        self.play(*[FadeOut(m) for m in (bx, base, lab, bits, bl, steps)])
        # wire format
        segs = [("‖x‖", 4, TEXT), ("‖r‖", 4, TEXT), ("3-bit indices", 24, GOLD), ("QJL signs", 32, OK)]
        u = 0.075
        packed = VGroup()
        for name, n, col in segs:
            r = Rectangle(width=n * u, height=0.5, stroke_color=BG, stroke_width=2, fill_color=col, fill_opacity=0.85)
            packed.add(r)
        packed.arrange(RIGHT, buff=0).move_to(LEFT * 3.8 + UP * 1.6, aligned_edge=LEFT).shift(LEFT * 1.6)
        plabs = VGroup(*[T(f"{n} B", 12, BG, weight="BOLD").move_to(r) for (nm, n, c), r in zip(segs, packed)])
        pn = VGroup(*[T(nm, 12, MUTED).next_to(r, UP, buff=0.05) for (nm, n, c), r in zip(segs, packed)])
        pt = T("packed: 64 B", 17, OK, weight="BOLD").next_to(packed, RIGHT, buff=0.2)
        f16 = Rectangle(width=128 * u, height=0.5, stroke_width=0, fill_color=COLD, fill_opacity=0.6)
        f16.move_to(packed.get_left() + DOWN * 1.0, aligned_edge=LEFT)
        f16t = T("FP16: 128 B", 17, COLD).next_to(f16, RIGHT, buff=0.2)
        self.play(FadeIn(packed, plabs, pn, pt))
        self.play(GrowFromEdge(f16, LEFT), FadeIn(f16t))
        self.caption("Per vector at head_dim 64: 64 bytes on the wire, 2× smaller than FP16 (the old '4×' was against FP32).", 1.2)
        est = M(r"\langle q, k\rangle \approx \langle q, \hat k\rangle + \|r\|\,\frac{\sqrt{\pi/2}}{m}\sum_{j=1}^{m} \operatorname{sign}(S r)_j\,(S q)_j", 30)
        est.move_to(LEFT * 1.2 + DOWN * 1.15)
        if est.width > 8.5:
            est.scale_to_fit_width(8.5)
        self.play(Write(est), run_time=1.5)
        res_t = T("Granite 3.3-2B, 40 layers: top-8 attention overlap 91.1% ± 3.3% (min 82.8%)", 17, OK)
        res_t.next_to(est, DOWN, buff=0.35)
        self.play(FadeIn(res_t))
        self.caption("Attention needs inner products, not exact vectors; the estimator corrects the quantized term with the sketch.", 2.4)


# --------------------------------------------------------------------------------------------- 12
class S12Storage(Captioned):
    tag = "12 · NVMe storage tier"

    def construct(self):
        gauge = Rectangle(width=0.35, height=2.4, stroke_color=EDGE, stroke_width=1.5).move_to(LEFT * 6.2 + UP * 1.0)
        fill = Rectangle(width=0.35, height=2.25, stroke_width=0, fill_color=BAD, fill_opacity=0.85)
        fill.move_to(gauge.get_bottom(), aligned_edge=DOWN)
        gl = TC("GPU KV\n93%", 14, BAD).next_to(gauge, DOWN, buff=0.1)
        dec = box(1.35, 0.5, color=SPILL, fill=BG, label="PMP: SPILL", size=14, label_color=SPILL).next_to(gauge, RIGHT, buff=0.3).shift(UP * 0.6)
        self.play(FadeIn(gauge, fill, gl), FadeIn(dec))
        self.caption("When the controller picks SPILL, StorageTier.spill(key, buf) queues the block and returns a future.")

        q = VGroup(*[Rectangle(width=0.55, height=0.5, stroke_color=EDGE, stroke_width=1.5, fill_color=BG, fill_opacity=1)
                     for _ in range(4)]).arrange(RIGHT, buff=0.06).move_to(LEFT * 2.6 + UP * 1.6)
        qt = T("coalesce = 4", 15, MUTED).next_to(q, UP, buff=0.08)
        file = VGroup(*[Rectangle(width=0.55, height=0.5, stroke_color=EDGE, stroke_width=1.2, fill_color=BG, fill_opacity=1)
                        for _ in range(16)]).arrange(RIGHT, buff=0).move_to(RIGHT * 0.2 + DOWN * 0.35)
        ftl = T("backing file on NVMe · 4096-byte aligned extents", 15, MUTED).next_to(file, DOWN, buff=0.1)
        self.play(FadeIn(q, qt), FadeIn(file, ftl))
        blocks = []
        for i in range(4):
            b = packet(SPILL, 0.5, 0.42, f"k{i}", 12).move_to(dec.get_center())
            self.play(FadeIn(b), b.animate.move_to(q[i]), run_time=0.35)
            blocks.append(b)
        self.caption("Every 4 queued blocks become one pwrite and one fdatasync: fewer syscalls, fewer flushes.")
        pw = T("pwrite + fdatasync", 16, SPILL, mono=True).move_to(LEFT * 0.4 + UP * 0.6)
        self.play(FadeIn(pw))
        self.play(*[b.animate.move_to(file[i + 2]) for i, b in enumerate(blocks)], run_time=0.9)
        self.play(*[file[i + 2].animate.set_fill(SPILL, 0.55) for i in range(4)], *[FadeOut(b) for b in blocks], FadeOut(pw))
        fill2 = Rectangle(width=0.35, height=1.75, stroke_width=0, fill_color=COLD, fill_opacity=0.85).move_to(gauge.get_bottom(), aligned_edge=DOWN)
        gl2 = TC("GPU KV\n73%", 14, COLD).move_to(gl)
        self.play(Transform(fill, fill2), Transform(gl, gl2))

        self.caption("delete(key) returns the extent to a free list; neighbors merge; the next spill reuses it first-fit.")
        self.play(file[3].animate.set_fill(BG, 1), file[4].animate.set_fill(BG, 1), run_time=0.5)
        br = Brace(VGroup(file[3], file[4]), DOWN, color=OK, buff=0.05)
        bt = T("merged free extent", 13, OK).next_to(br, DOWN, buff=0.05)
        self.play(FadeIn(br, bt), FadeOut(ftl))
        nb = packet(SPILL, 1.0, 0.42, "k7", 12).move_to(dec.get_center())
        self.play(FadeIn(nb), nb.animate.move_to(VGroup(file[3], file[4])), run_time=0.8)
        self.play(FadeOut(nb), file[3].animate.set_fill(SPILL, 0.55), file[4].animate.set_fill(SPILL, 0.55), FadeOut(br, bt))

        self.caption("retrieve(key): pread, then a CRC32 check, before the bytes go back to the GPU.")
        rb = packet(SPILL, 0.5, 0.42, "k3", 12).move_to(file[5])
        chk = T("crc32 ✓", 16, OK, weight="BOLD").move_to(LEFT * 0.4 + UP * 0.6)
        self.play(FadeIn(rb), rb.animate.move_to(LEFT * 0.4 + UP * 1.4), run_time=0.6)
        self.play(FadeIn(chk))
        self.play(rb.animate.move_to(gauge.get_center()), FadeOut(chk), file[5].animate.set_fill(BG, 1), run_time=0.7)
        self.play(FadeOut(rb))

        # measured coalescing sweep (Chimera)
        self.play(*[FadeOut(m) for m in (q, qt, file, dec, gauge, fill, gl)])
        data = [(1, 662, 1731), (10, 731, 2149), (20, 803, 2188), (50, 827, 1104)]
        ax = Axes(x_range=[0, 4, 1], y_range=[0, 2400, 600], x_length=7.5, y_length=3.6, tips=False,
                  axis_config={"color": EDGE, "include_ticks": False},
                  y_axis_config={"include_ticks": True, "include_numbers": False}).move_to(RIGHT * 0.3 + DOWN * 0.05)
        yl = VGroup(*[T(str(v), 13, MUTED).next_to(ax.c2p(0, v), LEFT, buff=0.1) for v in (0, 600, 1200, 1800, 2400)])
        ylab = T("MB/s", 14, MUTED).next_to(ax, UP, buff=0.05).align_to(ax, LEFT)
        bars = VGroup()
        for i, (c, w, r) in enumerate(data):
            xw = ax.c2p(i + 0.32, 0)[0]
            xr = ax.c2p(i + 0.68, 0)[0]
            for xx, v, col in ((xw, w, SPILL), (xr, r, COLD)):
                h = ax.c2p(0, v)[1] - ax.c2p(0, 0)[1]
                bar = Rectangle(width=0.55, height=h, stroke_width=0, fill_color=col, fill_opacity=0.85)
                bar.move_to([xx, ax.c2p(0, 0)[1] + h / 2, 0])
                val = T(str(v), 12, TEXT).next_to(bar, UP, buff=0.04)
                bars.add(VGroup(bar, val))
            bars.add(T(f"coalesce {c}", 14, MUTED).move_to([(xw + xr) / 2, ax.c2p(0, 0)[1] - 0.25, 0]))
        leg = VGroup(VGroup(Square(0.18, fill_color=SPILL, fill_opacity=0.85, stroke_width=0), T("write", 14, TEXT)).arrange(RIGHT, buff=0.08),
                     VGroup(Square(0.18, fill_color=COLD, fill_opacity=0.85, stroke_width=0), T("read", 14, TEXT)).arrange(RIGHT, buff=0.08)
                     ).arrange(RIGHT, buff=0.3).next_to(ax, UP, buff=0.05).align_to(ax, RIGHT)
        src = T("Chimera NVMe, 1.5 MiB KV blocks · benchmarks/results/test_arch/chimera_storage_spill.json", 13, MUTED)
        src.next_to(ax, DOWN, buff=0.45)
        self.play(Create(ax), FadeIn(yl, ylab, leg))
        self.play(LaggedStart(*[FadeIn(b, shift=UP * 0.2) for b in bars], lag_ratio=0.08), FadeIn(src), run_time=1.8)
        self.caption("Measured: writes gain from batching (662 → 827 MB/s); reads peak at 20 blocks and fall at 50 on this drive.", 2.6)
