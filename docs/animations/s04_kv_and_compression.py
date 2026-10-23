"""How the KV cache works, and how scuffedQuant differs from other KV compression."""
from __future__ import annotations

import numpy as np
from manim import *  # noqa: F401,F403

from style import (BAD, BG, COLD, EDGE, GOLD, HOT, MUTED, OK, PANEL, SPILL, TEXT, TC, Captioned, T, arrow, box,
                   packet)

KCOL, VCOL, QCOL = COLD, SPILL, HOT


def vec_bars(vals, col, w=0.11, gap=0.03, scale=0.28, base=None):
    """Small vertical bar chart for a vector; bars grow up/down from a baseline."""
    g = VGroup()
    for i, v in enumerate(vals):
        h = max(abs(v) * scale, 0.02)
        r = Rectangle(width=w, height=h, stroke_width=0, fill_color=col, fill_opacity=0.95)
        r.move_to([i * (w + gap), (h / 2 if v >= 0 else -h / 2), 0])
        g.add(r)
    line = Line(LEFT * 0.04, RIGHT * (len(vals) * (w + gap) - gap + 0.04), color=EDGE, stroke_width=1)
    return VGroup(line, g)


def hadamard(n):
    H = np.array([[1.0]])
    while H.shape[0] < n:
        H = np.block([[H, H], [H, -H]])
    return H


def M(tex, size=30, color=TEXT):
    return MathTex(tex, font_size=size, color=color)


# --------------------------------------------------------------------------------------------- 01a
class S01KVCache(Captioned):
    tag = "1 · how the KV cache works"

    def construct(self):
        rng = np.random.default_rng(16)
        words = ["The", "cat", "sat", "on", "the"]
        d = 4
        K = rng.normal(0, 1, (5, d))
        V = rng.normal(0, 1, (5, d))
        q = K[1] * 1.2 + rng.normal(0, 0.3, d)          # the new query looks most like "cat" (weight 0.85)

        # ---- part A: attention over cached keys and values
        Y_TOK, Y_K, Y_V, Y_S, Y_W = 2.55, 1.6, 0.55, -0.35, -0.62
        toks = VGroup(*[box(1.05, 0.5, color=EDGE, fill=PANEL, label=w, size=18) for w in words])
        toks.arrange(RIGHT, buff=0.22).move_to(LEFT * 1.6 + UP * Y_TOK)
        new = box(1.05, 0.5, color=HOT, fill=PANEL, label="mat ?", size=18).next_to(toks, RIGHT, buff=0.5)
        lab_x = toks.get_left()[0] - 0.3

        def rowlabel(s, y, col):
            t = T(s, 15, col)
            t.move_to([lab_x - t.width / 2, y, 0])
            return t

        self.play(LaggedStart(*[FadeIn(t, shift=DOWN * 0.15) for t in toks], lag_ratio=0.1), FadeIn(new))
        self.caption("Each token, in each attention layer, produces a key k and a value v. They describe the token for later tokens.")

        kb, vb = VGroup(), VGroup()
        for i, t in enumerate(toks):
            kb.add(vec_bars(K[i], KCOL).move_to([t.get_x(), Y_K, 0]))
            vb.add(vec_bars(V[i], VCOL).move_to([t.get_x(), Y_V, 0]))
        kl, vl = rowlabel("keys k", Y_K, KCOL), rowlabel("values v", Y_V, VCOL)
        self.play(LaggedStart(*[FadeIn(k, shift=DOWN * 0.1) for k in kb], lag_ratio=0.08),
                  LaggedStart(*[FadeIn(v, shift=DOWN * 0.1) for v in vb], lag_ratio=0.08), FadeIn(kl, vl), run_time=1.2)

        qb = vec_bars(q, QCOL).move_to([new.get_x(), Y_K, 0])
        ql = T("query q", 16, QCOL).next_to(qb, RIGHT, buff=0.2)
        self.play(FadeIn(qb, shift=DOWN * 0.1), FadeIn(ql))
        self.caption("To pick the next token, the new token's query is compared with every earlier key: one dot product each.")

        scores = K @ q / np.sqrt(d)
        w = np.exp(scores - scores.max())
        w = w / w.sum()
        stext = VGroup(*[T(f"{scores[i]:+.1f}", 15, TEXT, mono=True).move_to([toks[i].get_x(), Y_S, 0]) for i in range(5)])
        sl = rowlabel("q · k / √d", Y_S, MUTED)
        mover = qb.copy()
        for i in range(5):
            self.play(mover.animate.move_to(kb[i]), run_time=0.22)
            self.play(Indicate(kb[i], color=HOT, scale_factor=1.15), FadeIn(stext[i]), run_time=0.22)
        self.play(FadeOut(mover), FadeIn(sl))
        wb, wt = VGroup(), VGroup()
        for i in range(5):
            h = max(w[i] * 1.3, 0.03)
            r = Rectangle(width=0.5, height=h, stroke_width=0, fill_color=OK, fill_opacity=0.9)
            r.move_to([toks[i].get_x(), Y_W - h / 2, 0])
            wb.add(r)
            wt.add(T(f"{w[i]:.2f}", 13, OK, mono=True).next_to(r, DOWN, buff=0.06))
        wl = rowlabel("softmax weight", Y_W - 0.15, OK)
        self.play(LaggedStart(*[GrowFromEdge(r, UP) for r in wb], lag_ratio=0.1), FadeIn(wl), FadeIn(wt), run_time=0.9)
        self.caption("A softmax turns the scores into weights; the output is the weighted sum of the values. Here \"cat\" matters most.")

        out = (w[:, None] * V).sum(0)
        ob = vec_bars(out, OK).move_to([new.get_x(), Y_V - 0.9, 0])
        ol = T("output", 16, OK).next_to(ob, RIGHT, buff=0.2)
        copies = [vb[i].copy() for i in range(5)]
        self.play(*[c.animate.move_to(ob).set_opacity(0.25) for c in copies], run_time=0.9)
        self.play(*[FadeOut(c) for c in copies], FadeIn(ob), FadeIn(ol))
        att = M(r"\mathrm{attention}(q, K, V) = \mathrm{softmax}\!\left(\frac{q K^\top}{\sqrt{d}}\right) V", 30)
        att.to_edge(RIGHT, buff=0.4).set_y(-2.45)
        self.play(Write(att), run_time=1.0)
        self.wait(1.0)

        # ---- part B: the cache
        self.play(*[FadeOut(m) for m in (stext, sl, wb, wt, wl, ob, ol, att, qb, ql, new)])
        self.caption("Without a cache, every new token would recompute k and v for the whole prompt. The cache stores them once.")
        table_hdr = VGroup(T("token", 15, MUTED), T("k", 15, KCOL), T("v", 15, VCOL))
        cache = VGroup()
        title = T("KV cache (one layer)", 18, TEXT, weight="BOLD")
        rows = VGroup()
        for i, wd in enumerate(words):
            row = VGroup(T(wd, 15, TEXT), vec_bars(K[i], KCOL, scale=0.18), vec_bars(V[i], VCOL, scale=0.18))
            rows.add(row)
        grid_x = [0, 1.3, 2.4]

        def place(row, idx):
            for j, item in enumerate(row):
                item.move_to(RIGHT * (3.0 + grid_x[j]) + UP * (1.7 - idx * 0.48))
            return row

        title.move_to(RIGHT * 4.2 + UP * 3.1)
        for j, h in enumerate(table_hdr):
            h.move_to(RIGHT * (3.0 + grid_x[j]) + UP * 2.25)
        frame = RoundedRectangle(width=4.0, height=4.6, corner_radius=0.12, stroke_color=EDGE, stroke_width=1.5).move_to(RIGHT * 4.2 + UP * 0.45)
        for i, r in enumerate(rows):
            place(r, i)
        self.play(FadeIn(frame, title, table_hdr), LaggedStart(*[TransformFromCopy(VGroup(kb[i], vb[i]), rows[i]) for i in range(5)],
                                                              lag_ratio=0.12), run_time=1.4)
        for step, wd in enumerate(["mat", "and"]):
            nk, nv = rng.normal(0, 1, d), rng.normal(0, 1, d)
            row = place(VGroup(T(wd, 15, TEXT), vec_bars(nk, KCOL, scale=0.18), vec_bars(nv, VCOL, scale=0.18)), 5 + step)
            self.play(FadeIn(row, shift=LEFT * 0.3), Flash(row[0].get_left() + LEFT * 0.2, color=OK), run_time=0.6)
            rows.add(row)
        self.caption("Decode appends one row per token per layer, and every step reads the whole cache: it keeps growing.")
        self.wait(0.6)

        # ---- part C: size
        self.play(*[FadeOut(m) for m in (toks, kb, vb, kl, vl)])
        size = VGroup(
            M(r"\text{bytes per token} = 2 \times L \times h_{kv} \times d \times b", 32),
            M(r"= 2 \times 40 \times 8 \times 64 \times 2 = 80\ \text{KiB}", 32, OK),
            T("Granite 3.3-2B: 40 layers, 8 KV heads, head_dim 64, bf16", 16, MUTED),
            T("2,048-token prompt → 160 MiB, per request", 20, TEXT),
        ).arrange(DOWN, buff=0.25, aligned_edge=LEFT).move_to(LEFT * 3.2 + UP * 1.0)
        self.play(Write(size[0]), run_time=1.0)
        self.play(Write(size[1]), FadeIn(size[2]), run_time=1.0)
        self.play(FadeIn(size[3]))
        self.caption("The 2 is for K and V. It is per token and per request, so long contexts and many requests add up fast.")
        self.wait(0.8)

        # ---- part D: paged blocks
        self.play(FadeOut(size), FadeOut(rows), FadeOut(frame), FadeOut(title), FadeOut(table_hdr))
        self.caption("vLLM stores the cache in fixed blocks of 16 tokens and keeps a block table, like virtual memory pages.")
        logical = VGroup(*[box(1.5, 0.55, color=HOT if i == 2 else COLD, fill=PANEL, label=f"block {i}", size=15) for i in range(3)])
        logical.arrange(DOWN, buff=0.18).move_to(LEFT * 4.6 + UP * 0.6)
        ll = T("request's blocks", 16, MUTED).next_to(logical, UP, buff=0.2)
        gpu = VGroup(*[Rectangle(width=0.55, height=0.42, stroke_color=EDGE, stroke_width=1.2, fill_color=BG, fill_opacity=1) for _ in range(24)])
        gpu.arrange_in_grid(rows=4, cols=6, buff=0.06).move_to(RIGHT * 2.6 + UP * 0.6)
        gl = T("GPU memory: physical blocks", 16, MUTED).next_to(gpu, UP, buff=0.2)
        self.play(FadeIn(logical, ll, gpu, gl))
        phys = [7, 2, 17]
        arrows = VGroup()
        for i, p in enumerate(phys):
            a = Arrow(logical[i].get_right(), gpu[p].get_left(), buff=0.08, color=MUTED, stroke_width=2, tip_length=0.14)
            arrows.add(a)
            self.play(GrowArrow(a), gpu[p].animate.set_fill(HOT if i == 2 else COLD, 0.8), run_time=0.45)
        self.caption("Blocks need not be contiguous, so at most one partly empty block per request. A KV transfer moves these blocks.")
        self.wait(0.8)

        # ---- part E: prefill vs decode, and why it moves
        self.play(*[FadeOut(m) for m in (logical, ll, gpu, gl, arrows)])
        pre = box(4.0, 2.2, color=COLD).move_to(LEFT * 3.9 + UP * 0.5)
        pre_t = VGroup(T("prefill", 22, COLD, weight="BOLD"), T("whole prompt at once", 16, TEXT),
                       T("writes every row of the cache", 16, TEXT), T("compute-bound", 16, MUTED)).arrange(DOWN, buff=0.12).move_to(pre)
        dec = box(4.0, 2.2, color=HOT).move_to(RIGHT * 3.9 + UP * 0.5)
        dec_t = VGroup(T("decode", 22, HOT, weight="BOLD"), T("one token per step", 16, TEXT),
                       T("reads the whole cache each step", 16, TEXT), T("memory-bandwidth-bound", 16, MUTED)).arrange(DOWN, buff=0.12).move_to(dec)
        self.play(FadeIn(pre, pre_t, shift=RIGHT * 0.2), FadeIn(dec, dec_t, shift=LEFT * 0.2))
        mv = packet(COLD, 1.5, 0.45, "KV cache", 16).move_to(pre.get_right() + RIGHT * 0.95)
        self.play(FadeIn(mv))
        self.play(mv.animate.move_to(dec.get_left() + LEFT * 0.95), run_time=1.0)
        sv = VGroup(T("server 1", 15, MUTED).next_to(pre, DOWN, buff=0.12), T("server 2", 15, MUTED).next_to(dec, DOWN, buff=0.12))
        self.play(FadeIn(sv))
        self.caption("Disaggregated serving runs the two phases on different servers, so the cache must cross the network.", 2.2)


# --------------------------------------------------------------------------------------------- 11b
class S11Compare(Captioned):
    tag = "11 · how scuffedQuant differs from other KV compression"

    def construct(self):
        x = np.array([0.3, -0.2, 2.9, 0.1, -0.4, 0.2, 0.1, -0.3])     # one key with an outlier channel
        inp = vec_bars(x, KCOL, w=0.16, gap=0.05, scale=0.32)
        inl = T("same key, one outlier channel", 15, MUTED)
        g0 = VGroup(inp, inl).arrange(DOWN, buff=0.15).move_to(RIGHT * 3.4 + UP * 2.75)
        self.play(FadeIn(g0))
        self.caption("Four ways to shrink the KV cache. They differ in what they keep and where they run.")

        rows = [
            ("FP8 cast", "vLLM --kv-cache-dtype fp8", "8-bit float per number + a scale", "GPU cache for every token", COLD),
            ("KIVI (2-bit)", "Liu et al., ICML 2024", "2 bits + scale and zero per group;\nnewest tokens kept full precision", "GPU cache for every token", GOLD),
            ("Token eviction", "H2O, StreamingLLM", "keeps some tokens exactly,\ndrops the rest", "GPU cache: dropped tokens\ncan't be attended to", BAD),
            ("scuffedQuant", "TurboQuant / QJL recipe", "random rotation, 3 bits per number,\n256-bit sketch of the error", "per transfer: wire and NVMe;\nGPU cache stays bf16", OK),
        ]
        cards = VGroup()
        for name, src, what, where, col in rows:
            bg = RoundedRectangle(width=12.6, height=1.05, corner_radius=0.1, stroke_color=col, stroke_width=2,
                                  fill_color=PANEL, fill_opacity=1)
            n = VGroup(T(name, 19, col, weight="BOLD"), T(src, 12, MUTED)).arrange(DOWN, buff=0.05, aligned_edge=LEFT)
            n.move_to(bg.get_left() + RIGHT * 1.45)
            wt = TC(what, 14, TEXT, buff=0.03).move_to(bg.get_center() + LEFT * 0.35)
            wh = TC(where, 14, MUTED, buff=0.03).move_to(bg.get_right() + LEFT * 2.0)
            cards.add(VGroup(bg, n, wt, wh))
        cards.arrange(DOWN, buff=0.1).move_to(DOWN * 0.85)
        hy = cards.get_top()[1] + 0.22
        hdr = VGroup(T("method", 14, MUTED).move_to([cards[0][1].get_x(), hy, 0]).align_to(cards[0][1], LEFT),
                     T("what it stores", 14, MUTED).move_to([cards[0][2].get_x(), hy, 0]),
                     T("where it applies", 14, MUTED).move_to([cards[0][3].get_x(), hy, 0]))
        self.play(FadeIn(hdr))
        for i, c in enumerate(cards):
            self.play(FadeIn(c, shift=UP * 0.15), run_time=0.5)
            self.wait(1.4 if i < 3 else 0.6)
        self.caption("Rotation spreads the outlier over all channels, so one 3-bit codebook fits without per-group scales.")
        signs = np.random.default_rng(42).choice([-1.0, 1.0], 8)
        y = hadamard(8) @ (signs * x) / np.sqrt(8)                       # the real random-sign Hadamard rotation
        rotated = vec_bars(y, OK, w=0.16, gap=0.05, scale=0.32)
        rotated.move_to(inp)
        inl2 = T("after the rotation: no outlier", 15, OK).move_to(inl)
        self.play(Transform(inp, rotated), Transform(inl, inl2), cards[3][0].animate.set_stroke(OK, 3.5), run_time=1.2)
        self.wait(1.2)

        # ---- bytes per vector
        self.play(FadeOut(cards), FadeOut(hdr), FadeOut(g0))
        self.caption("Bytes per K or V vector (arithmetic). At head_dim 64 scuffedQuant ties FP8; at 128 it is smaller.")
        methods = [("bf16", [128, 256], TEXT), ("FP8", [64, 128], COLD), ("scuffedQuant", [64, 88], OK)]
        ax_x = [-3.2, 3.2]
        chart = VGroup()
        for gi, dlabel in enumerate(["head_dim 64", "head_dim 128"]):
            cx = ax_x[gi]
            base = Line(LEFT * 2.4 + RIGHT * cx + DOWN * 1.9, RIGHT * 2.4 + RIGHT * cx + DOWN * 1.9, color=EDGE, stroke_width=2)
            lab = T(dlabel, 18, TEXT, weight="BOLD").next_to(base, DOWN, buff=0.45)
            chart.add(base, lab)
            for mi, (mname, vals, col) in enumerate(methods):
                h = vals[gi] / 256 * 3.6
                bx = cx + (mi - 1) * 1.45
                r = Rectangle(width=1.0, height=h, stroke_width=0, fill_color=col, fill_opacity=0.85)
                r.move_to([bx, -1.9 + h / 2, 0])
                v = T(f"{vals[gi]} B", 15, TEXT).next_to(r, UP, buff=0.06)
                nm = T(mname, 13, MUTED).next_to(base, DOWN, buff=0.08).set_x(bx)
                chart.add(VGroup(r, v, nm))
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.15) for c in chart], lag_ratio=0.05), run_time=1.6)
        formula = M(r"\text{scuffedQuant: } 4 + 4 + \tfrac{3d}{8} + \tfrac{256}{8}\ \text{bytes}", 28, OK).to_edge(UP, buff=0.8)
        self.play(Write(formula))
        kv = T("KIVI's 2 bits are smaller still (plus scales and a full-precision window), but it changes the GPU cache.", 15, MUTED)
        kv.next_to(formula, DOWN, buff=0.25)
        self.play(FadeIn(kv))
        self.wait(1.6)

        # ---- where it runs
        self.play(FadeOut(chart), FadeOut(formula), FadeOut(kv))
        self.caption("The math follows TurboQuant and QJL. What's different is where it runs: only on bytes that leave the GPU.")
        g1 = box(2.6, 1.0, color=COLD, label="server 1 GPU\nKV cache (bf16)", size=15).move_to(LEFT * 5.0 + UP * 1.3)
        pol = box(2.6, 1.0, color=GOLD, label="policy rule: link ≥ 80%,\ncold, ≥ 256 KiB → compress", size=15).move_to(LEFT * 1.8 + UP * 1.3)
        enc = box(2.3, 1.0, color=OK, label="scuffedQuant\nencode (64 B/vec)", size=15).move_to(RIGHT * 1.2 + UP * 1.3)
        wire = box(2.0, 1.0, color=EDGE, label="RDMA wire\nor NVMe", size=15).move_to(RIGHT * 3.75 + UP * 1.3)
        g2 = box(2.4, 1.0, color=HOT, label="server 2: rebuild\nbf16, into its cache", size=15).move_to(RIGHT * 5.0 + DOWN * 0.7)
        arrs = VGroup(arrow(g1.get_right(), pol.get_left(), MUTED), arrow(pol.get_right(), enc.get_left(), MUTED),
                      arrow(enc.get_right(), wire.get_left(), MUTED), arrow(wire.get_bottom(), g2.get_top(), MUTED))
        skip = CurvedArrow(pol.get_bottom() + DOWN * 0.05, wire.get_bottom() + LEFT * 0.4 + DOWN * 0.05, angle=0.6,
                           color=MUTED, stroke_width=2, tip_length=0.14)
        skt = T("link idle: send raw bf16", 14, MUTED).next_to(skip, DOWN, buff=0.08)
        self.play(LaggedStart(FadeIn(g1), GrowArrow(arrs[0]), FadeIn(pol), GrowArrow(arrs[1]), FadeIn(enc),
                              GrowArrow(arrs[2]), FadeIn(wire), GrowArrow(arrs[3]), FadeIn(g2), lag_ratio=0.25), run_time=2.4)
        self.play(Create(skip), FadeIn(skt))
        note = T("FP8, KIVI and eviction change the GPU cache for every token; scuffedQuant only touches bytes that leave the GPU.",
                 15, TEXT).move_to(DOWN * 2.2)
        if note.width > 12.8:
            note.scale_to_fit_width(12.8)
        self.play(FadeIn(note))
        self.wait(1.0)
        self.caption("In the vLLM connector it is a config switch today; wiring the policy rule in is open.", 1.8)
        self.caption("There the receiver rebuilds from the 3-bit part alone, so the sketch goes unused on that path for now.", 2.0)
        self.caption("Not measured yet: quality vs FP8 and KIVI on the same KV. So far: 91.1% top-8 overlap with the sketch.", 2.4)
