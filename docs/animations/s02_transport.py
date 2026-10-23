"""Transport scenes: the dual pool on libfabric, the blob channel, completion signaling, the vLLM connector."""
from __future__ import annotations

from manim import *  # noqa: F401,F403

from style import (BAD, BG, COLD, EDGE, GOLD, HOT, MUTED, OK, PANEL, SPILL, TEXT, TC, Captioned, T, arrow, box,
                   packet)


def lines(spec, size=15, color=TEXT, buff=0.08):
    return VGroup(*[T(s, size, c if c else color, mono=m) for s, c, m in spec]).arrange(DOWN, buff=buff,
                                                                                     aligned_edge=LEFT)


# --------------------------------------------------------------------------------------------- 04
class S04DualPool(Captioned):
    tag = "4 · the dual pool on libfabric"

    def construct(self):
        frame = RoundedRectangle(width=8.4, height=5.6, corner_radius=0.15, stroke_color=EDGE, stroke_width=2,
                                 fill_color=PANEL, fill_opacity=0.5).move_to(LEFT * 2.4 + UP * 0.15)
        ft = T("libscuffedfabric", 20, TEXT, weight="BOLD").next_to(frame.get_top(), DOWN, buff=0.12)
        dom = box(7.8, 0.55, color=EDGE, fill=BG, label="fabric + domain  (shared when provider and endpoint type match)",
                  size=15).next_to(ft, DOWN, buff=0.15)
        arena = VGroup(*[Rectangle(width=0.6, height=0.4, stroke_color=EDGE, stroke_width=1.2, fill_color=BG,
                                   fill_opacity=1) for _ in range(12)]).arrange(RIGHT, buff=0)
        arena.next_to(dom, DOWN, buff=0.25)
        at = T("one registered arena (fi_mr_reg)", 15, MUTED).next_to(arena, DOWN, buff=0.06)
        self.play(FadeIn(frame, ft), FadeIn(dom), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(a) for a in arena], lag_ratio=0.05), FadeIn(at), run_time=0.8)

        hot = box(3.7, 2.3, color=HOT)
        hl = lines([("HOT endpoint", HOT, False), ("FI_EP_MSG or FI_EP_RDM", None, True),
                    ("busy-poll CQ, or fi_cntr", None, False), ("FI_SELECTIVE_COMPLETION", None, True),
                    ("inject for ≤ inject_size", None, False)], 15).move_to(hot)
        cold = box(3.7, 2.3, color=COLD)
        cl = lines([("COLD endpoint", COLD, False), ("FI_EP_MSG or FI_EP_RDM", None, True),
                    ("512-entry tx queue (hot: 64)", None, False), ("CQ with FI_WAIT_UNSPEC", None, True),
                    ("fi_cq_sread: thread sleeps", None, False)], 15).move_to(cold)
        eps = VGroup(VGroup(hot, hl), VGroup(cold, cl)).arrange(RIGHT, buff=0.35).next_to(at, DOWN, buff=0.25)
        self.play(FadeIn(eps[0], shift=UP * 0.2), FadeIn(eps[1], shift=UP * 0.2))
        self.caption("Each class gets its own endpoint and completion style; both share one domain and memory region.")

        # completion behavior: hot spins, cold sleeps then wakes
        spin = Arc(radius=0.2, angle=PI * 1.4, color=HOT, stroke_width=4).move_to(hot.get_corner(UR) + DL * 0.35)
        zz = T("z z", 18, COLD).move_to(cold.get_corner(UR) + DL * 0.35)
        self.play(FadeIn(spin), FadeIn(zz))
        self.play(Rotate(spin, -2 * TAU, about_point=spin.get_center()), zz.animate.shift(UP * 0.1).set_opacity(0.4),
                  run_time=1.6, rate_func=linear)
        ev = packet(COLD, 0.5, 0.26, "CQE", 11).move_to(cold.get_bottom() + DOWN * 0.3)
        self.play(FadeIn(ev, shift=UP * 0.2), Rotate(spin, -TAU, about_point=spin.get_center()), run_time=0.6)
        self.play(ev.animate.move_to(zz), FadeOut(zz), Flash(cold.get_corner(UR) + DL * 0.35, color=COLD),
                  Rotate(spin, -TAU, about_point=spin.get_center()), run_time=0.6)
        self.play(FadeOut(ev))
        self.caption("Hot spins for the lowest latency; cold sleeps on a wait object and wakes per completion.", 0.8)

        # providers per class
        provs = VGroup(*[box(2.6, 0.5, color=EDGE, fill=BG, label=p, size=15) for p in
                         ["verbs  ·  MSG", "verbs;ofi_rxm  ·  RDM", "tcp  ·  MSG / RDM", "shm  ·  RDM"]])
        provs.arrange(DOWN, buff=0.14).move_to(RIGHT * 4.85 + UP * 0.9)
        ptitle = T("provider per class", 17, MUTED).next_to(provs, UP, buff=0.15)
        self.play(FadeIn(ptitle), LaggedStart(*[FadeIn(p, shift=LEFT * 0.2) for p in provs], lag_ratio=0.12))
        a1 = arrow(provs[1].get_left(), hot.get_right() + UP * 0.6, HOT)
        a2 = arrow(provs[0].get_left(), cold.get_right() + UP * 0.2, COLD)
        self.play(GrowArrow(a1), GrowArrow(a2), provs[1][0].animate.set_stroke(HOT, 3),
                  provs[0][0].animate.set_stroke(COLD, 3))
        note = TC("mixed config: hot RDM + cold MSG\nneeds two domains,\nso the arena is registered twice", 15, MUTED)
        note.next_to(provs, DOWN, buff=0.3)
        self.play(FadeIn(note))
        self.caption("Provider and endpoint type are per class, chosen at run time. Experiment E4 compares the mixes.", 1.8)

        # mapping table
        self.play(*[FadeOut(m) for m in [frame, ft, dom, arena, at, eps, spin, provs, ptitle, a1, a2, note]])
        rows = [("RC QP per class", "endpoint per class (MSG or RDM)"),
                ("RDMA_WRITE_WITH_IMM", "fi_writedata (+ remote CQ data)"),
                ("send CQ + completion channel", "CQ wait object, fi_cq_sread"),
                ("(no equivalent)", "fi_cntr remote-write counter"),
                ("QPN/PSN/GID over TCP", "passive endpoint, or fi_av_insert")]
        hdr = VGroup(T("libibverbs  (libscuffedverbs)", 19, MUTED, weight="BOLD"),
                     T("libfabric  (libscuffedfabric)", 19, OK, weight="BOLD"))
        tab = VGroup()
        for a, b in rows:
            ra = box(5.4, 0.55, color=EDGE, fill=PANEL, label=a, size=16)
            rb = box(5.4, 0.55, color=OK, fill=PANEL, label=b, size=16)
            tab.add(VGroup(ra, rb).arrange(RIGHT, buff=0.9))
        tab.arrange(DOWN, buff=0.14).move_to(UP * 0.1)
        hdr[0].next_to(tab[0][0], UP, buff=0.2)
        hdr[1].next_to(tab[0][1], UP, buff=0.2)
        self.play(FadeIn(hdr))
        for r in tab:
            ar = arrow(r[0].get_right(), r[1].get_left(), OK, buff=0.08)
            self.play(FadeIn(r[0]), GrowArrow(ar), FadeIn(r[1], shift=LEFT * 0.2), run_time=0.55)
        self.caption("Both libraries export scuffed_fabric.h, so sf_bench and sv_bench are one benchmark source.", 2.5)


# --------------------------------------------------------------------------------------------- 05
class S05BlobChannel(Captioned):
    tag = "5 · FabricBlobChannel: credits and one-sided writes"

    def _arena(self, title, x):
        segs = VGroup()
        for i in range(4):
            segs.add(Rectangle(width=0.62, height=0.55, stroke_color=COLD, stroke_width=1.5, fill_color=BG, fill_opacity=1))
        for i in range(4):
            segs.add(Rectangle(width=0.62, height=0.55, stroke_color=EDGE, stroke_width=1.5, fill_color=BG, fill_opacity=1))
        segs.add(Rectangle(width=0.45, height=0.55, stroke_color=HOT, stroke_width=1.5, fill_color=BG, fill_opacity=1))
        segs.arrange(RIGHT, buff=0).move_to(RIGHT * x + UP * 1.3)
        t = T(title, 19, TEXT, weight="BOLD").next_to(segs, UP, buff=0.32)
        l1 = T("recv slots", 13, COLD).next_to(VGroup(*segs[:4]), UP, buff=0.05)
        l2 = T("staging", 13, MUTED).next_to(VGroup(*segs[4:8]), UP, buff=0.05)
        l3 = T("scratch", 11, HOT).next_to(segs[8], UP, buff=0.05)
        nums = VGroup(*[T(str(i), 13, MUTED, mono=True).move_to(segs[i]) for i in range(4)] +
                      [T(str(i), 13, MUTED, mono=True).move_to(segs[4 + i]) for i in range(4)])
        return segs, VGroup(t, l1, l2, l3, nums)

    def construct(self):
        s_segs, s_lab = self._arena("sender (prefill)", -3.55)
        r_segs, r_lab = self._arena("receiver (decode)", 3.55)
        hot_lane = Line(LEFT * 6.2 + DOWN * 0.35, RIGHT * 6.2 + DOWN * 0.35, color=HOT, stroke_width=8, stroke_opacity=0.35)
        cold_lane = Line(LEFT * 6.2 + DOWN * 1.15, RIGHT * 6.2 + DOWN * 1.15, color=COLD, stroke_width=8, stroke_opacity=0.35)
        hlt = T("hot endpoint", 14, HOT).next_to(hot_lane, UP, buff=0.04).shift(LEFT * 4.6)
        clt = T("cold endpoint", 14, COLD).next_to(cold_lane, UP, buff=0.04).shift(LEFT * 4.6)
        self.play(FadeIn(s_segs, s_lab, r_segs, r_lab), Create(hot_lane), Create(cold_lane), FadeIn(hlt, clt))

        credits = VGroup(*[Circle(0.17, color=OK, fill_color=OK, fill_opacity=0.85, stroke_width=0) for _ in range(4)])
        credits.arrange(RIGHT, buff=0.12).move_to(LEFT * 3.55 + DOWN * 2.15)
        cnum = VGroup(*[T(str(i), 13, BG, weight="BOLD", mono=True).move_to(c) for i, c in enumerate(credits)])
        ctl = T("credits = free slots at the receiver", 14, OK).next_to(credits, DOWN, buff=0.1)
        self.play(FadeIn(credits, cnum, ctl))
        self.caption("Each side's region: receive slots the peer writes into, local staging, scratch for credits.")

        blob = packet(COLD, 1.5, 0.45, "layer 7 KV", 14).move_to(LEFT * 6.0 + UP * 2.9)
        self.play(FadeIn(blob, shift=RIGHT * 0.3))
        # take credit 2
        self.caption("To send: take a credit, copy header + key + chunk into the matching staging slot.")
        self.play(credits[2].animate.set_fill(EDGE, 0.5), cnum[2].animate.set_opacity(0.3))
        st = s_segs[4 + 2]
        self.play(blob.animate.scale(0.38).move_to(st), st.animate.set_fill(COLD, 0.6), run_time=0.7)
        hdr = VGroup(T("64-byte header", 15, TEXT, weight="BOLD"),
                     T("magic · blob_id · key_len · flags", 13, MUTED, mono=True),
                     T("total · chunk_off · chunk_len", 13, MUTED, mono=True)).arrange(DOWN, buff=0.06)
        hdr.move_to(UP * 2.75 + LEFT * 0.0)
        self.play(FadeIn(hdr))

        # data write
        self.caption("One fi_writedata puts the chunk in the peer's slot 2 and carries imm = DATA | 2.")
        pk = packet(COLD, 0.95, 0.38, "DATA|2", 13).move_to(st.get_bottom() + DOWN * 1.05)
        self.play(FadeIn(pk), run_time=0.3)
        self.play(pk.animate.move_to(RIGHT * 3.55 + DOWN * 1.15), run_time=1.0, rate_func=linear)
        tgt = r_segs[2]
        self.play(pk.animate.scale(0.6).move_to(tgt), tgt.animate.set_fill(COLD, 0.7), run_time=0.5)
        cqe = box(1.9, 0.48, color=COLD, fill=BG, label="CQ: DATA | slot 2", size=14).move_to(RIGHT * 3.55 + DOWN * 2.15)
        self.play(FadeIn(cqe, shift=UP * 0.2), FadeOut(pk), FadeOut(blob))
        self.caption("Payload and notification are one operation on one endpoint: the event can't overtake its data.", 1.2)

        # deliver + credit back
        out = packet(COLD, 1.5, 0.45, "layer 7 KV", 14).move_to(RIGHT * 6.0 + UP * 2.9).set_opacity(0)
        self.play(out.animate.set_opacity(1), tgt.animate.set_fill(BG, 1), FadeOut(cqe), run_time=0.6)
        self.caption("The receiver copies the chunk out, then returns the slot: an 8-byte write on the hot endpoint.")
        cr = packet(HOT, 1.15, 0.36, "CREDIT|2", 12).move_to(RIGHT * 3.55 + DOWN * 0.35)
        sc = r_segs[8]
        self.play(sc.animate.set_fill(HOT, 0.7), FadeIn(cr), run_time=0.3)
        self.play(cr.animate.move_to(LEFT * 3.55 + DOWN * 0.35), run_time=0.7, rate_func=linear)
        self.play(cr.animate.scale(0.5).move_to(credits[2]), FadeOut(cr), credits[2].animate.set_fill(OK, 0.85),
                  cnum[2].animate.set_opacity(1), st.animate.set_fill(BG, 1), sc.animate.set_fill(BG, 1), run_time=0.6)
        self.caption("Credits ride the hot endpoint, so they don't wait behind KV on the cold one.", 1.2)

        # pipelined burst
        self.caption("With four credits, four chunks are in flight; the sender stalls only when every slot is full.")
        flights = []
        for i in range(4):
            p = packet(COLD, 0.55, 0.3).move_to(LEFT * 3.55 + DOWN * 1.15)
            flights.append(p)
        self.play(*[credits[i].animate.set_fill(EDGE, 0.5) for i in range(4)],
                  LaggedStart(*[Succession(FadeIn(p, run_time=0.1),
                                           p.animate(run_time=0.6, rate_func=linear).move_to(RIGHT * 3.55 + DOWN * 1.15),
                                           p.animate(run_time=0.3).move_to(r_segs[i]), FadeOut(p, run_time=0.1))
                                for i, p in enumerate(flights)], lag_ratio=0.25), run_time=2.4)
        backs = [packet(HOT, 0.4, 0.26).move_to(RIGHT * 3.55 + DOWN * 0.35) for _ in range(4)]
        self.play(LaggedStart(*[Succession(FadeIn(b, run_time=0.05),
                                           b.animate(run_time=0.5, rate_func=linear).move_to(LEFT * 3.55 + DOWN * 0.35),
                                           b.animate(run_time=0.3).move_to(credits[i]), FadeOut(b, run_time=0.05))
                                for i, b in enumerate(backs)], lag_ratio=0.25),
                  *[credits[i].animate.set_fill(OK, 0.85) for i in range(4)], run_time=2.2)
        self.wait(1.2)


# --------------------------------------------------------------------------------------------- 06
class S06Completion(Captioned):
    tag = "6 · how the receiver learns data arrived"

    def construct(self):
        mechs = [
            ("CQ data", "fi_writedata: the immediate lands in the target's CQ", "a posted receive per write"),
            ("flag in payload", "receiver spins on the last bytes of the buffer", "NIC placing the last bytes last"),
            ("sentinel write", "a second 8-byte write after the payload", "write-after-write ordering (shm: no)"),
            ("remote-write counter", "fi_cntr on the target counts arrivals", "FI_RMA_EVENT (tcp: did not count)"),
            ("write + 8-byte read", "the read returns only after the write is placed", "one extra round trip"),
        ]
        rows = VGroup()
        for name, how, needs in mechs:
            n = T(name, 18, TEXT, weight="BOLD")
            rows.add(n)
        rows.arrange(DOWN, buff=0.62, aligned_edge=LEFT).move_to(LEFT * 5.3 + UP * 0.35)

        snd = []
        bufs = []
        for r in rows:
            s = Dot(color=MUTED).move_to(RIGHT * -3.25 + UP * r.get_center()[1])
            b = VGroup(*[Rectangle(width=0.32, height=0.34, stroke_color=EDGE, stroke_width=1.2, fill_color=BG,
                                   fill_opacity=1) for _ in range(6)]).arrange(RIGHT, buff=0)
            b.move_to(RIGHT * -0.75 + UP * r.get_center()[1])
            snd.append(s)
            bufs.append(b)
        hd1 = T("initiator", 15, MUTED).next_to(snd[0], UP, buff=0.3)
        hd2 = T("target buffer", 15, MUTED).next_to(bufs[0], UP, buff=0.18)
        self.play(FadeIn(rows), *[FadeIn(s) for s in snd], *[FadeIn(b) for b in bufs], FadeIn(hd1, hd2))
        self.caption("Five ways to signal completion of a one-sided write. All five are in sf_bench -m sig.")

        notes = VGroup()
        for i, (name, how, needs) in enumerate(mechs):
            y = rows[i].get_center()[1]
            pay = packet(COLD, 1.6, 0.3).move_to(snd[i])
            self.play(FadeIn(pay, run_time=0.1))
            self.play(pay.animate.move_to(bufs[i][:5]).stretch_to_fit_width(1.6), run_time=0.5, rate_func=linear)
            self.play(FadeOut(pay, run_time=0.1), *[c.animate.set_fill(COLD, 0.7) for c in bufs[i][:5]], run_time=0.2)
            sig_pos = bufs[i].get_right() + RIGHT * 0.6
            if i == 0:
                cq = box(0.95, 0.36, color=HOT, fill=BG, label="CQE+imm", size=12).move_to(sig_pos + RIGHT * 0.15)
                self.play(FadeIn(cq, scale=0.7), run_time=0.3)
                sig = cq
            elif i == 1:
                self.play(bufs[i][5].animate.set_fill(HOT, 0.9), run_time=0.3)
                sig = Arc(radius=0.17, angle=PI * 1.5, color=HOT, stroke_width=3).move_to(sig_pos)
                self.play(FadeIn(sig), Rotate(sig, -TAU, about_point=sig.get_center()), run_time=0.5)
            elif i == 2:
                s2 = packet(HOT, 0.3, 0.3).move_to(snd[i])
                self.play(s2.animate.move_to(bufs[i][5]), run_time=0.45)
                self.play(bufs[i][5].animate.set_fill(HOT, 0.9), FadeOut(s2), run_time=0.15)
                sig = T("WAW", 13, HOT, weight="BOLD").move_to(sig_pos)
                self.play(FadeIn(sig), run_time=0.2)
            elif i == 3:
                ctr = ValueTracker(41)
                sig = always_redraw(lambda c=ctr, p=sig_pos: T(f"cntr {int(c.get_value())}", 14, HOT, mono=True)
                                    .move_to(p + RIGHT * 0.2))
                self.add(sig)
                self.play(ctr.animate.set_value(42), run_time=0.3)
            else:
                rd = packet(HOT, 0.3, 0.22).move_to(snd[i])
                self.play(rd.animate.move_to(bufs[i][5]), run_time=0.35)
                self.play(rd.animate.move_to(snd[i]), run_time=0.35)
                self.play(Flash(snd[i].get_center(), color=HOT), FadeOut(rd), run_time=0.3)
                sig = T("read done", 13, HOT).move_to(sig_pos + RIGHT * 0.15)
                self.play(FadeIn(sig), run_time=0.2)
            nt = VGroup(T(how, 16, TEXT), T("needs: " + needs, 16, MUTED)).arrange(DOWN, buff=0.04, aligned_edge=LEFT)
            if nt.width > 5.0:
                nt.scale_to_fit_width(5.0)
            nt.move_to(RIGHT * 1.85 + UP * y, aligned_edge=LEFT)
            self.play(FadeIn(nt, shift=LEFT * 0.1), run_time=0.3)
            notes.add(nt)
            self.wait(0.9)
        self.caption("The counter is libfabric's form of fabric-lib's ImmCounter; write + read is the GPFS flush pattern.", 1.6)
        self.caption("Experiment E5: p99 and user-space instructions per post for each. Adopt one only if it moves p99.", 2.2)


# --------------------------------------------------------------------------------------------- 07
class S07Connector(Captioned):
    tag = "7 · ScuffedRdmaConnector inside vLLM"

    def construct(self):
        cols = {"client": -5.9, "proxy": -3.3, "prefill": -0.3, "decode": 4.6}
        heads = VGroup()
        lifelines = VGroup()
        for name, x in cols.items():
            sub = {"client": "", "proxy": "proxy.py", "prefill": "vLLM · kv_producer", "decode": "vLLM · kv_consumer"}[name]
            h = box(2.3 if name in ("prefill", "decode") else 1.6, 0.7, color=EDGE)
            h.move_to(RIGHT * x + UP * 2.85)
            ht = VGroup(T(name, 18, TEXT, weight="BOLD"), T(sub, 12, MUTED)).arrange(DOWN, buff=0.03).move_to(h) if sub \
                else T(name, 18, TEXT, weight="BOLD").move_to(h)
            heads.add(VGroup(h, ht))
            lifelines.add(DashedLine(h.get_bottom(), RIGHT * x + DOWN * 3.1, color=EDGE, stroke_width=1.5))
        self.play(FadeIn(heads), Create(lifelines))

        y = [2.15]
        shown = VGroup()

        def msg(a, b, text, color=MUTED, size=14, dy=0.42, self_note=False):
            yy = y[0]
            if self_note:
                if a == "decode":
                    t = T(text, size, color).move_to(RIGHT * (cols[a] - 0.2) + UP * yy, aligned_edge=RIGHT)
                else:
                    t = T(text, size, color).move_to(RIGHT * (cols[a] + 0.2) + UP * yy, aligned_edge=LEFT)
                bar = Line(RIGHT * cols[a] + UP * (yy + 0.15), RIGHT * cols[a] + UP * (yy - 0.15), color=color, stroke_width=6)
                self.play(FadeIn(bar), FadeIn(t, shift=RIGHT * 0.1), run_time=0.45)
                y[0] -= dy
                shown.add(VGroup(bar, t))
                return VGroup(bar, t)
            ar = Arrow(RIGHT * cols[a] + UP * yy, RIGHT * cols[b] + UP * yy, buff=0.05, color=color, stroke_width=3,
                       max_tip_length_to_length_ratio=0.06, tip_length=0.16)
            t = T(text, size, color).next_to(ar, UP, buff=0.03)
            self.play(GrowArrow(ar), FadeIn(t), run_time=0.5)
            y[0] -= dy
            shown.add(VGroup(ar, t))
            return VGroup(ar, t)

        self.caption("A request goes to prefill first, with max_tokens=1 and a transfer id.")
        msg("client", "proxy", "POST /v1/completions", TEXT)
        msg("proxy", "prefill", "prompt · max_tokens=1 · xfer_id", TEXT)
        self.wait(1.2)
        self.caption("Each attention layer's save_kv_layer gathers the blocks, copies to host, encodes, queues a blob.")
        msg("prefill", "prefill", "save_kv_layer × 40: gather → host copy → encode", MUTED, self_note=True, dy=0.5)
        self.wait(1.0)
        for k, lab in enumerate(["xfer_id/layer.0  (cold)", "xfer_id/layer.1  (cold)", "…  layer.39  (cold)"]):
            msg("prefill", "decode", lab, COLD, dy=0.34)
        msg("prefill", "decode", "xfer_id/__done__  (hot)", HOT)
        self.caption("The WFA tags each blob; bulk layers go cold, the done marker goes hot.", 1.8)
        msg("prefill", "proxy", "kv_transfer_params", TEXT)
        msg("proxy", "decode", "full request + kv_transfer_params", TEXT)
        self.wait(1.0)
        self.caption("Decode claims the prompt as external tokens, waits per layer, scatters into its paged cache.")
        msg("decode", "decode", "start_load_kv: wait per layer → scatter", MUTED, self_note=True, dy=0.5)
        seq = msg("decode", "client", "tokens stream back (through the proxy)", OK)
        self.wait(1.5)

        side = VGroup(
            T("if something fails", 16, BAD, weight="BOLD"),
            T("layer missing after 30 s →", 14, TEXT),
            T("get_block_ids_with_load_errors,", 13, MUTED, mono=True),
            T("vLLM recomputes those blocks", 14, TEXT),
            T("libfabric won't open →", 14, TEXT),
            T("TCP channel + tcp_fallback event", 14, TEXT),
        ).arrange(DOWN, buff=0.07, aligned_edge=LEFT)
        frame = SurroundingRectangle(side, color=BAD, buff=0.15, corner_radius=0.1)
        panel = BackgroundRectangle(VGroup(side, frame), color=BG, fill_opacity=0.95, buff=0.1)
        VGroup(panel, side, frame).move_to(RIGHT * 0.6 + DOWN * 0.3)
        self.wait(1.0)
        self.caption("Failures degrade instead of hanging: recompute missing layers, fall back to TCP, and say so.")
        self.play(shown.animate.set_opacity(0.18), FadeIn(panel), FadeIn(side), Create(frame))
        self.wait(3.5)
