"""Problem scenes: overview, the traffic (network + storage), head-of-line blocking, industry landscape."""
from __future__ import annotations

from manim import *  # noqa: F401,F403

from style import (BAD, BG, COLD, EDGE, GOLD, HOT, MUTED, OK, PANEL, SPILL, TEXT, TC, Captioned, T, arrow, box,
                   packet)


# --------------------------------------------------------------------------------------------- 00
class S00Overview(Captioned):
    tag = "ScuffedRDMA · overview"

    def construct(self):
        title = T("ScuffedRDMA", 64, TEXT, weight="BOLD")
        sub = T("adaptive RDMA middleware for disaggregated LLM inference over commodity Ethernet", 24, MUTED)
        g = VGroup(title, sub).arrange(DOWN, buff=0.35)
        self.play(Write(title), run_time=1.2)
        self.play(FadeIn(sub, shift=UP * 0.2))
        self.wait(1.2)
        self.play(FadeOut(g, shift=UP * 0.4))

        # pipeline of the four control stages
        stages = [("Telemetry", "signal vector"), ("WFA", "cold · warm · hot"),
                  ("Policy tree", "rules over signals"), ("PMP", "hot · cold · spill")]
        sb = VGroup()
        for name, desc in stages:
            b = box(2.5, 1.05, color=EDGE)
            n = T(name, 24, TEXT, weight="BOLD").move_to(b.get_center() + UP * 0.17)
            d = T(desc, 16, MUTED).move_to(b.get_center() + DOWN * 0.22)
            sb.add(VGroup(b, n, d))
        sb.arrange(RIGHT, buff=0.5).move_to(UP * 1.95)
        arrs = VGroup(*[arrow(sb[i].get_right(), sb[i + 1].get_left(), MUTED, buff=0.05) for i in range(3)])

        pre = box(1.7, 3.0, label=None).move_to(LEFT * 5.9 + DOWN * 1.05)
        pre_t = TC("prefill\nGPU", 20, TEXT, weight="BOLD").move_to(pre)
        dec = box(1.7, 2.1, label=None).move_to(RIGHT * 5.9 + DOWN * 0.6)
        dec_t = TC("decode\nGPU", 20, TEXT, weight="BOLD").move_to(dec)
        nvme = box(1.7, 0.75, color=SPILL, label="NVMe · GPFS", size=16).move_to(RIGHT * 5.9 + DOWN * 2.15)

        lanes = VGroup()
        ys = [-0.15, -0.95, -2.15]
        cols = [HOT, COLD, SPILL]
        names = ["hot endpoint · busy-poll", "cold endpoint · deep queue", "spill · coalesced pwrite"]
        for y, c, nm in zip(ys, cols, names):
            ln = Line(LEFT * 4.9 + UP * y, RIGHT * 4.9 + UP * y, color=c, stroke_width=10, stroke_opacity=0.35)
            lab = T(nm, 15, c).next_to(ln, DOWN, buff=0.1).align_to(ln, LEFT).shift(RIGHT * 0.15)
            lanes.add(VGroup(ln, lab))
        self.play(LaggedStart(*[FadeIn(s, shift=DOWN * 0.2) for s in sb], lag_ratio=0.15),
                  Create(arrs), FadeIn(pre, pre_t, dec, dec_t, nvme), run_time=1.6)
        self.play(LaggedStart(*[Create(l[0]) for l in lanes], lag_ratio=0.2),
                  LaggedStart(*[FadeIn(l[1]) for l in lanes], lag_ratio=0.2), run_time=1.2)
        self.caption("Every transfer is measured, classified, routed by policy, then placed on a queue.")

        examples = [
            (packet(HOT, 0.36, 0.36), ["32 B · token", "hot", "control-hot", "σH lowest"], 0, "token id, decode step"),
            (packet(COLD, 1.0, 0.42, "4 MiB"), ["4 MiB · prefill", "cold", "prefill-bulk-cold", "σC lowest"], 1,
             "one layer of prefill KV"),
            (packet(SPILL, 1.0, 0.42, "4 MiB"), ["GPU 93% full", "cold", "spill-under-pressure", "σS lowest"], 2,
             "same block, GPU memory past the watermark"),
        ]
        for pk, notes, lane, what in examples:
            pk.move_to(pre.get_top() + DOWN * 0.5)
            self.play(FadeIn(pk, scale=0.6), run_time=0.35)
            self.play(pk.animate.move_to(sb[0].get_bottom() + DOWN * 0.45), run_time=0.45)
            tags = VGroup()
            for i, s in enumerate(notes):
                t = T(s, 14, cols[lane] if i else TEXT).next_to(sb[i], DOWN, buff=0.1)
                tags.add(t)
                self.play(pk.animate.move_to(sb[i].get_bottom() + DOWN * 0.45),
                          Indicate(sb[i][0], color=cols[lane], scale_factor=1.04), FadeIn(t), run_time=0.42)
            tgt_y = ys[lane]
            self.play(pk.animate.move_to(LEFT * 4.4 + UP * tgt_y), FadeOut(tags), run_time=0.45)
            dest = nvme if lane == 2 else dec
            self.play(pk.animate.move_to(RIGHT * 4.4 + UP * tgt_y), run_time=1.0 if lane else 0.45,
                      rate_func=linear)
            self.play(pk.animate.scale(0.4).move_to(dest), run_time=0.3)
            self.play(FadeOut(pk), run_time=0.2)

        self.caption("Small decode traffic never waits behind bulk in its own queue; bulk spills when memory runs out.")
        flow = []
        for k in range(14):
            lane = [0, 1, 0, 0, 1, 2, 0, 1, 0, 0, 1, 0, 2, 0][k]
            w = 0.3 if lane == 0 else 0.9
            p = packet(cols[lane], w, 0.3 if lane == 0 else 0.4).move_to(LEFT * 4.6 + UP * ys[lane])
            flow.append(p)
        self.play(LaggedStart(*[Succession(FadeIn(p, run_time=0.1),
                                           p.animate(run_time=0.9 if i % 3 else 1.6, rate_func=linear)
                                           .move_to(RIGHT * 4.6 + UP * p.get_center()[1]),
                                           FadeOut(p, run_time=0.1))
                                for i, p in enumerate(flow)], lag_ratio=0.18), run_time=5)
        self.wait(0.5)


# --------------------------------------------------------------------------------------------- 01
class S01Traffic(Captioned):
    tag = "1 · what moves: network and storage"

    def construct(self):
        pre = box(4.0, 4.3).move_to(LEFT * 4.65 + UP * 0.35)
        pre_h = T("Server 1 · prefill", 22, TEXT, weight="BOLD").next_to(pre.get_top(), DOWN, buff=0.15)
        pre_s = T("2× RTX 5090", 15, MUTED).next_to(pre_h, DOWN, buff=0.06)
        dec = box(4.0, 4.3).move_to(RIGHT * 4.65 + UP * 0.35)
        dec_h = T("Server 2 · decode", 22, TEXT, weight="BOLD").next_to(dec.get_top(), DOWN, buff=0.15)
        dec_s = T("3× RTX 3090", 15, MUTED).next_to(dec_h, DOWN, buff=0.06)
        link = Line(LEFT * 2.6 + UP * 0.6, RIGHT * 2.6 + UP * 0.6, color=EDGE, stroke_width=14)
        link_t = T("10 GbE · SoftRoCE", 16, MUTED).next_to(link, UP, buff=0.1)
        self.play(FadeIn(pre, pre_h, pre_s, dec, dec_h, dec_s), Create(link), FadeIn(link_t))

        # 8 layer bars stand for 40 layers
        layers = VGroup(*[Rectangle(width=2.6, height=0.22, stroke_color=EDGE, stroke_width=1.5,
                                    fill_color=PANEL, fill_opacity=1) for _ in range(8)])
        layers.arrange(UP, buff=0.08).move_to(pre.get_center() + DOWN * 0.45 + RIGHT * 0.35)
        ltag = TC("40 layers\n(8 shown)", 13, MUTED).next_to(layers, LEFT, buff=0.15)
        prompt = VGroup(*[Square(0.11, stroke_width=0, fill_color=TEXT, fill_opacity=0.85) for _ in range(16)])
        prompt.arrange(RIGHT, buff=0.04).next_to(pre, DOWN, buff=0.25)
        ptag = T("2,048-token prompt", 15, MUTED).next_to(prompt, DOWN, buff=0.08)

        grid = VGroup(*[Rectangle(width=0.4, height=0.3, stroke_color=EDGE, stroke_width=1.2,
                                  fill_color=BG, fill_opacity=1) for _ in range(40)])
        grid.arrange_in_grid(rows=5, cols=8, buff=0.05).move_to(dec.get_center() + DOWN * 0.55 + LEFT * 0.25)
        gtag = T("paged KV cache", 14, MUTED).next_to(grid, UP, buff=0.08)
        gauge = Rectangle(width=0.22, height=1.7, stroke_color=EDGE, stroke_width=1.5).next_to(grid, RIGHT, buff=0.25)
        fill = Rectangle(width=0.22, height=0.001, stroke_width=0, fill_color=COLD, fill_opacity=0.9)
        fill.align_to(gauge, DOWN).move_to(gauge.get_bottom(), aligned_edge=DOWN)
        mark = DashedLine(gauge.get_corner(UL) + DOWN * 0.17 + LEFT * 0.08, gauge.get_corner(UR) + DOWN * 0.17 + RIGHT * 0.08,
                          color=BAD, stroke_width=2)
        gl = TC("GPU\nmem", 12, MUTED).next_to(gauge, DOWN, buff=0.06)
        self.play(FadeIn(layers, ltag, prompt, ptag, grid, gtag, gauge, gl, mark), run_time=0.8)

        self.caption("Prefill reads the prompt once and writes KV for every layer: 2 KiB per token per layer.")
        self.play(prompt.animate.move_to(layers.get_bottom() + DOWN * 0.3), run_time=0.6)
        self.play(FadeOut(prompt), run_time=0.2)

        sent = ValueTracker(0)
        ctr = always_redraw(lambda: T(f"KV sent  {sent.get_value():5.0f} / 160 MiB", 18, COLD, mono=True)
                            .next_to(link, DOWN, buff=0.18))
        self.add(ctr)
        cells = list(grid)
        for i, lay in enumerate(layers):
            blk = packet(COLD, 0.8, 0.26, "4 MiB", 12).move_to(lay)
            self.play(lay.animate.set_fill(COLD, 0.55), FadeIn(blk, scale=0.8), run_time=0.18)
            tgt = VGroup(*cells[i * 5:(i + 1) * 5])
            self.play(blk.animate.move_to(link.get_start() + DOWN * 0.0), run_time=0.22)
            self.play(blk.animate.move_to(link.get_end()), sent.animate.set_value(20 * (i + 1)),
                      run_time=0.42, rate_func=linear)
            self.play(Transform(blk, tgt.copy().set_fill(COLD, 0.85).set_stroke(COLD, 1)),
                      tgt.animate.set_fill(COLD, 0.85),
                      fill.animate.stretch_to_fit_height(0.17 * (i + 1) * 1.05).move_to(gauge.get_bottom(), aligned_edge=DOWN),
                      run_time=0.2)
            self.remove(blk)
            if i == 1:
                self.caption("A 2,048-token prompt: 4 MiB per layer, 160 MiB in all, about 134 ms on a 10 Gb/s wire.")
        self.wait(0.6)

        self.caption("Meanwhile other requests need small, urgent messages: control blobs, credits, metadata, token ids.")
        for k in range(6):
            a = packet(HOT, 0.26, 0.26).move_to(link.get_start() + UP * 0.0)
            b = packet(HOT, 0.26, 0.26).move_to(link.get_end())
            self.play(FadeIn(a), FadeIn(b), run_time=0.1)
            self.play(a.animate.move_to(link.get_end()), b.animate.move_to(link.get_start()), run_time=0.45,
                      rate_func=linear)
            self.play(FadeOut(a), FadeOut(b), run_time=0.1)
        sizes = T("32 B to 256 KiB, every decode step", 16, HOT).next_to(link_t, UP, buff=0.1)
        self.play(FadeIn(sizes))
        self.wait(0.8)

        # storage: memory pressure -> spill
        nv = box(2.2, 0.65, color=SPILL, label="local NVMe", size=16).next_to(dec, DOWN, buff=0.35)
        self.caption("When decode GPU memory passes the watermark, cold KV spills to NVMe instead of being dropped.")
        self.play(FadeIn(nv), FadeOut(sizes))
        self.play(fill.animate.stretch_to_fit_height(1.62).move_to(gauge.get_bottom(), aligned_edge=DOWN)
                  .set_fill(BAD, 0.9), run_time=0.8)
        out = VGroup(*cells[:10])
        moving = out.copy().set_fill(SPILL, 0.9).set_stroke(SPILL, 1)
        self.play(out.animate.set_fill(BG, 1), moving.animate.arrange_in_grid(rows=2, cols=5, buff=0.03)
                  .scale(0.5).move_to(nv), run_time=1.0)
        self.play(FadeOut(moving), nv[0].animate.set_fill(SPILL, 0.25),
                  fill.animate.stretch_to_fit_height(1.2).move_to(gauge.get_bottom(), aligned_edge=DOWN)
                  .set_fill(COLD, 0.9), run_time=0.6)
        self.caption("All of it shares one link and one GPU. The thesis: keep the small transfers fast while bulk streams.")
        self.wait(2)


# --------------------------------------------------------------------------------------------- 02
class S02HeadOfLine(Captioned):
    tag = "2 · head-of-line blocking"

    def _pipe(self, y, label, color=EDGE):
        p = RoundedRectangle(width=8.6, height=0.8, corner_radius=0.1, stroke_color=color, stroke_width=2,
                             fill_color=PANEL, fill_opacity=1).move_to(LEFT * 1.4 + UP * y)
        t = T(label, 16, MUTED).next_to(p, UP, buff=0.08).align_to(p, LEFT)
        return VGroup(p, t)

    def construct(self):
        wire = box(1.6, 3.2, color=EDGE).move_to(RIGHT * 4.95 + UP * 0.2)
        wt = TC("NIC + wire\n10 Gb/s", 17, TEXT).next_to(wire, UP, buff=0.12)
        q = self._pipe(0.2, "one queue pair: everything in order")
        self.play(FadeIn(wire, wt, q))
        self.caption("One queue pair carries both kinds of traffic, in order.")

        x0 = q[0].get_right()[0] - 0.85
        blocks = VGroup(*[packet(COLD, 1.45, 0.56, "1 MiB", 15) for _ in range(4)])
        for i, b in enumerate(blocks):
            b.move_to(RIGHT * (x0 - i * 1.55) + UP * 0.2)
        hot = packet(HOT, 0.42, 0.42, "4K", 13).move_to(RIGHT * (x0 - 4 * 1.55 + 0.4) + UP * 0.2)
        self.play(LaggedStart(*[FadeIn(b, shift=RIGHT * 0.5) for b in blocks], lag_ratio=0.15), run_time=0.9)
        self.play(FadeIn(hot, shift=RIGHT * 0.3))
        hl = T("decode-critical, 4 KiB", 15, HOT).next_to(hot, DOWN, buff=0.45)
        self.play(FadeIn(hl))

        waited = ValueTracker(0)
        timer = always_redraw(lambda: T(f"hot message waited  {waited.get_value():.2f} ms", 22, HOT, mono=True)
                              .move_to(UP * 2.3 + LEFT * 1.4))
        self.add(timer)
        self.caption("Each 1 MiB block ahead takes about 0.84 ms to serialize at 10 Gb/s (8.39 Mbit / 10 Gb/s).")
        for i in range(4):
            head = blocks[i]
            rest = VGroup(*blocks[i + 1:], hot, hl)
            self.play(head.animate.move_to(wire.get_center()).scale(0.6), rest.animate.shift(RIGHT * 1.55),
                      waited.animate.set_value(0.839 * (i + 1)), run_time=0.95, rate_func=linear)
            self.play(FadeOut(head, run_time=0.15))
        self.play(hot.animate.move_to(wire.get_center()), FadeOut(hl), run_time=0.4)
        self.play(FadeOut(hot), Flash(wire.get_center(), color=HOT), run_time=0.4)
        self.caption("Four blocks ahead: 3.36 ms before a 4 KiB message even starts. That lands in TTFT and p99.", 1.6)

        # dual pool
        self.remove(timer)
        self.play(FadeOut(q))
        qh = self._pipe(1.0, "hot endpoint: small, latency-critical", HOT)
        qc = self._pipe(-0.6, "cold endpoint: bulk, deep queue", COLD)
        self.play(FadeIn(qh, qc))
        blocks = VGroup(*[packet(COLD, 1.45, 0.56, "1 MiB", 15) for _ in range(4)])
        for i, b in enumerate(blocks):
            b.move_to(RIGHT * (x0 - i * 1.55) + DOWN * 0.6)
        hot = packet(HOT, 0.42, 0.42, "4K", 13).move_to(RIGHT * (x0 - 4 * 1.55 + 0.4) + UP * 1.0)
        waited.set_value(0)
        timer2 = always_redraw(lambda: T(f"hot message waited  {waited.get_value():.2f} ms", 22, OK, mono=True)
                               .move_to(UP * 2.3 + LEFT * 1.4))
        self.add(timer2)
        self.play(FadeIn(blocks), FadeIn(hot), run_time=0.6)
        self.caption("Dual pool: the hot message has nothing ahead of it in its own queue.")
        self.play(hot.animate.move_to(wire.get_center()), blocks[0].animate.move_to(wire.get_center()).scale(0.6),
                  VGroup(*blocks[1:]).animate.shift(RIGHT * 1.55), waited.animate.set_value(0.0), run_time=0.95,
                  rate_func=linear)
        self.play(FadeOut(hot), FadeOut(blocks[0]), Flash(wire.get_center(), color=OK), run_time=0.4)
        for i in range(1, 4):
            self.play(blocks[i].animate.move_to(wire.get_center()).scale(0.6),
                      VGroup(*blocks[i + 1:]).animate.shift(RIGHT * 1.55), run_time=0.7, rate_func=linear)
            self.play(FadeOut(blocks[i]), run_time=0.1)
        self.caption("The NIC and wire are still shared. Experiment E3 measures what that costs on SoftRoCE.", 2.2)


# --------------------------------------------------------------------------------------------- 03
class S03Landscape(Captioned):
    tag = "3 · where industry stands"

    def construct(self):
        rows = [
            ("serving", ["vLLM", "SGLang", "Ray RDT"]),
            ("KV connectors", ["NIXL", "Mooncake", "LMCache"]),
            ("transport stacks", ["UCX", "libfabric", "DOCA"]),
            ("verbs", ["libibverbs / rdma-core"]),
            ("NICs", ["ConnectX", "EFA", "Slingshot", "SoftRoCE"]),
        ]
        stack = VGroup()
        chips = {}
        for i, (name, items) in enumerate(rows):
            r = RoundedRectangle(width=7.4, height=0.82, corner_radius=0.1, stroke_color=EDGE, stroke_width=2,
                                 fill_color=PANEL, fill_opacity=1)
            lab = T(name, 16, MUTED).move_to(r.get_left() + RIGHT * 1.05)
            cs = VGroup()
            for it in items:
                c = box(max(1.05, len(it) * 0.13 + 0.4), 0.48, color=EDGE, fill=BG, label=it, size=15)
                cs.add(c)
                chips[it] = c
            cs.arrange(RIGHT, buff=0.12).move_to(r.get_center() + RIGHT * 0.95)
            stack.add(VGroup(r, lab, cs))
        stack.arrange(DOWN, buff=0.14).move_to(LEFT * 2.95 + UP * 0.25)
        self.play(LaggedStart(*[FadeIn(r, shift=UP * 0.15) for r in stack], lag_ratio=0.15), run_time=1.4)
        self.caption("The disaggregated-serving stack, top to bottom.")

        issues = [
            ("Built for bulk", "RDT, Mooncake, NIXL and LMCache move\nhomogeneous bulk. None classes mixed\nhot/cold traffic on a shared link.", 1),
            ("libfabric path is EFA-shaped", "NIXL's LIBFABRIC backend picks cxi, efa,\ntcp, sockets; verbs is not on the list,\nand it requires GPUDirect RDMA.", 2),
            ("Library side effects", "Mistral traced a 400 MB/min vLLM leak\nto UCX's mmap hooks (NIXL disagg path).", 2),
            ("Silent fallback", "GPFS APAR IV61625: no reconnect after\na QP error; traffic quietly moves to TCP.", 3),
            ("Unchecked completions", "Our early pool counted failed writes as\nfast ones. The 8 µs figure is withdrawn.", 3),
        ]
        card_prev = None
        for k, (head, body, row) in enumerate(issues):
            card = VGroup()
            bg = RoundedRectangle(width=5.2, height=1.55, corner_radius=0.12, stroke_color=BAD, stroke_width=2,
                                  fill_color=PANEL, fill_opacity=1)
            h = T("⚠ " + head, 19, BAD, weight="BOLD").move_to(bg.get_top() + DOWN * 0.3).align_to(bg, LEFT).shift(RIGHT * 0.2)
            b = T(body, 15, TEXT, line_spacing=0.9).next_to(h, DOWN, buff=0.12).align_to(h, LEFT)
            card.add(bg, h, b)
            card.move_to(RIGHT * 4.25 + UP * 0.25)
            ar = arrow(card.get_left(), stack[row][0].get_right(), BAD, buff=0.08)
            anims = [FadeIn(card, shift=LEFT * 0.2), GrowArrow(ar), stack[row][0].animate.set_stroke(BAD, 2.5)]
            if card_prev is not None:
                anims += [FadeOut(card_prev[0]), FadeOut(card_prev[1]), card_prev[2].animate.set_stroke(EDGE, 2)]
            self.play(*anims, run_time=0.6)
            if k == 0:
                self.caption("Five problems that show up once small and large transfers share hardware.")
            self.wait(2.2)
            card_prev = (card, ar, stack[row][0])
        self.play(FadeOut(card_prev[0]), FadeOut(card_prev[1]), card_prev[2].animate.set_stroke(EDGE, 2))

        # where the thesis sits
        ours = [
            (1, "ScuffedRdmaConnector"),
            (2, "libscuffedfabric · libscuffedverbs"),
        ]
        adds = VGroup()
        for row, text in ours:
            c = box(len(text) * 0.12 + 0.5, 0.5, color=OK, fill=BG, label=text, size=15, label_color=OK)
            c.move_to(stack[row][0].get_right() + RIGHT * (c.width / 2 + 0.25))
            adds.add(c)
        self.play(LaggedStart(*[FadeIn(a, shift=LEFT * 0.3) for a in adds], lag_ratio=0.3),
                  chips["libfabric"][0].animate.set_stroke(OK, 3), chips["SoftRoCE"][0].animate.set_stroke(OK, 3),
                  chips["vLLM"][0].animate.set_stroke(OK, 3), run_time=1.0)
        cell = VGroup(
            T("this thesis", 20, OK, weight="BOLD"),
            T("mixed hot/cold traffic", 17, TEXT),
            T("commodity 10 GbE, SoftRoCE", 17, TEXT),
            T("no GPUDirect, host staging", 17, TEXT),
        ).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        frame = SurroundingRectangle(cell, color=OK, buff=0.2, corner_radius=0.1)
        VGroup(cell, frame).move_to(RIGHT * 4.6 + DOWN * 1.55)
        self.play(FadeIn(cell), Create(frame))
        self.caption("The thesis sits in the cell nobody covers: mixed traffic on commodity Ethernet.", 2.5)
