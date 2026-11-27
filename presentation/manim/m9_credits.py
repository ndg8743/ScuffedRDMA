"""M9: the blob channel. A credit is the right to write into one receive slot."""
from style import *

N = 8


class M9Credits(Clip):
    def construct(self):
        sh, pitch = 0.5, 0.6
        top = 2.2
        ys = [top - i * pitch for i in range(N)]
        xs, xr = -4.85, 4.15
        sw = 1.9
        send = RoundedRectangle(width=3.7, height=N * pitch + 0.55, corner_radius=0.12, stroke_color=EDGE, stroke_width=3, fill_color=PANEL, fill_opacity=1).move_to([xs - 0.2, (ys[0] + ys[-1]) / 2, 0])
        recv = RoundedRectangle(width=3.0, height=N * pitch + 0.55, corner_radius=0.12, stroke_color=EDGE, stroke_width=3, fill_color=PANEL, fill_opacity=1).move_to([xr, (ys[0] + ys[-1]) / 2, 0])
        sl = T("sender, 8 staging slots", size=30).next_to(send, UP, buff=0.15)
        rl = T("receiver, 8 slots of 4 MiB", size=30).next_to(recv, UP, buff=0.15)
        ss = [Rectangle(width=sw, height=sh, stroke_color=EDGE, stroke_width=2.5, fill_color=BG, fill_opacity=1).move_to([xs - 0.75, y, 0]) for y in ys]
        rs = [Rectangle(width=sw, height=sh, stroke_color=EDGE, stroke_width=2.5, fill_color=BG, fill_opacity=1).move_to([xr, y, 0]) for y in ys]
        cx = xs + 0.95
        cr = [Dot([cx, y, 0], radius=0.16, color=HOTF).set_stroke(HOT, 2) for y in ys]
        cl = T("credits", size=28, color=HOT).move_to([cx, ys[-1] - 0.78, 0])
        leg = VGroup(
            VGroup(Rectangle(width=0.7, height=0.36, stroke_color=COLD, stroke_width=2.5, fill_color=COLDF, fill_opacity=1), T("chunk, cold endpoint", size=28, color=COLD)).arrange(RIGHT, buff=0.2),
            VGroup(Dot(radius=0.14, color=HOTF).set_stroke(HOT, 2), T("credit, 8 bytes, hot endpoint", size=28, color=HOT)).arrange(RIGHT, buff=0.2),
        ).arrange(DOWN, buff=0.18, aligned_edge=LEFT).move_to([-0.35, ys[-1] + 0.1, 0])
        self.add(send, recv, sl, rl, *ss, *rs, *cr, cl, leg)
        self.caption("A credit is the right to write into one receive slot", run_time=0)
        self.wait(2.4)

        def chunk_at(i):
            return Rectangle(width=sw - 0.1, height=sh - 0.1, stroke_color=COLD, stroke_width=2.5, fill_color=COLDF, fill_opacity=1).move_to(ss[i])

        # one slow cycle on slot 0
        self.caption("The sender spends a credit and writes a chunk into that slot")
        c0 = chunk_at(0)
        self.play(cr[0].animate.set_opacity(0.15), FadeIn(c0), run_time=0.6)
        self.play(c0.animate.move_to(rs[0]), run_time=1.3, rate_func=smooth)
        tagB = T("in use", size=26, color=COLD).next_to(recv, RIGHT, buff=0.12).set_y(ys[0])
        self.play(FadeIn(tagB), run_time=0.3)
        self.wait(0.5)
        self.caption("The receiver copies the chunk out, and then returns the credit")
        tagC = T("copied", size=26, color=OKC).move_to(tagB).align_to(tagB, LEFT)
        self.play(c0.animate.set_fill(BG, 1).set_stroke(OKC, 3), FadeOut(tagB), FadeIn(tagC), run_time=0.6)
        back = Dot(rs[0].get_left() + LEFT * 0.2, radius=0.16, color=HOTF).set_stroke(HOT, 2)
        self.play(FadeIn(back), run_time=0.2)
        self.play(back.animate.move_to(cr[0]), run_time=1.1, rate_func=smooth)
        self.play(FadeOut(back), cr[0].animate.set_opacity(1), FadeOut(c0), FadeOut(tagC), run_time=0.4)
        self.wait(0.4)

        # the whole window in flight
        self.caption("At most 8 slots of 4 MiB are in flight: a window of 32 MiB")
        chunks = [chunk_at(i) for i in range(N)]
        self.play(*[cr[i].animate.set_opacity(0.15) for i in range(N)], *[FadeIn(c) for c in chunks], run_time=0.5)
        self.play(LaggedStart(*[chunks[i].animate.move_to(rs[i]) for i in range(N)], lag_ratio=0.12), run_time=2.0)
        wait = T("no credit: the sender waits", size=30, color=INK, weight=BOLD).move_to([0, 1.2, 0])
        self.play(FadeIn(wait), run_time=0.4)
        self.wait(1.0)
        backs = [Dot(rs[i].get_left() + LEFT * 0.2, radius=0.16, color=HOTF).set_stroke(HOT, 2) for i in range(N)]
        self.play(FadeOut(wait), *[chunks[i].animate.set_fill(BG, 1).set_stroke(OKC, 3) for i in range(N)], run_time=0.5)
        self.play(LaggedStart(*[AnimationGroup(FadeIn(backs[i]), backs[i].animate.move_to(cr[i])) for i in range(N)], lag_ratio=0.12), run_time=2.0)
        self.play(*[FadeOut(b) for b in backs], *[cr[i].animate.set_opacity(1) for i in range(N)], *[FadeOut(c) for c in chunks], run_time=0.4)

        self.caption("So throughput is at most the window divided by the credit round trip")
        f = M(r"X \;\le\; \frac{N\,B}{t_{\mathrm{credit}}}", size=56, color=NAVY).move_to([0, 1.0, 0])
        self.play(Write(f), run_time=1.2)
        self.hold()
