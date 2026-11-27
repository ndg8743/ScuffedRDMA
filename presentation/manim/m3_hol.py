"""M3: head-of-line blocking in one send queue, and one queue per class."""
from style import *


def block(w, kind, label=None, h=0.8, size=28):
    if kind == "hot":
        r = RoundedRectangle(width=w, height=h, corner_radius=0.07, stroke_color=HOT, stroke_width=3,
                             fill_color=HOTF, fill_opacity=1)
    else:
        r = RoundedRectangle(width=w, height=h, corner_radius=0.07, stroke_color=COLD, stroke_width=3,
                             fill_color=COLDF, fill_opacity=1)
    g = VGroup(r)
    if label:
        g.add(T(label, size=size, color=INK).move_to(r))
    return g


class M3HeadOfLine(Clip):
    def construct(self):
        # ---------- one queue ----------
        y = 1.55
        lane = Line([-6.6, y - 0.62, 0], [3.0, y - 0.62, 0], color=EDGE, stroke_width=4)
        lane2 = Line([-6.6, y + 0.62, 0], [3.0, y + 0.62, 0], color=EDGE, stroke_width=4)
        ql = T("one send queue", size=30, color=MUTED).move_to([-5.2, y + 1.05, 0])
        wire = Rectangle(width=2.9, height=0.6, stroke_color=EDGE, stroke_width=3, fill_color=PANEL, fill_opacity=1).move_to([4.9, y, 0])
        wl = T("link", size=30, color=MUTED).next_to(wire, UP, buff=0.2)
        step = 1.62
        xs = [2.1 - step * k for k in range(4)]
        colds = [block(1.45, "cold", "1 MiB").move_to([x, y, 0]) for x in xs]
        hot = block(0.5, "hot").move_to([xs[3] - 1.25, y, 0])
        hl = T("64 bytes", size=30, color=HOT).next_to(hot, DOWN, buff=0.75)
        ha = Line(hl.get_top(), hot.get_bottom(), color=HOT, stroke_width=3, buff=0.05)
        tr = ValueTracker(0.0)
        clock = DecimalNumber(0, num_decimal_places=2, font_size=56, color=NAVY)
        clock.add_updater(lambda m: m.set_value(tr.get_value()))
        cu = T("ms waited", size=32, color=NAVY)
        VGroup(clock, cu).arrange(RIGHT, buff=0.2).move_to([4.9, y - 1.4, 0])
        cu.add_updater(lambda m: m.next_to(clock, RIGHT, buff=0.2, aligned_edge=DOWN))
        self.add(lane, lane2, ql, wire, wl, *colds, hot, hl, ha, clock, cu)
        self.caption("A message of 64 bytes arrives behind four blocks of 1 MiB", run_time=0)
        self.wait(2.4)
        self.caption("Each block holds the 10 gigabit link for 0.84 ms")
        for k in range(4):
            rest = colds[k + 1:] + [hot, hl, ha]
            self.play(colds[k].animate.move_to(wire.get_center()), run_time=0.3, rate_func=linear)
            self.play(tr.animate.set_value(0.8389 * (k + 1)), FadeOut(colds[k], shift=RIGHT * 1.6),
                      *[m.animate.shift(RIGHT * step) for m in rest], run_time=0.9, rate_func=linear)
        tr.set_value(3.36)
        self.play(hot.animate.move_to(wire.get_center()), FadeOut(hl), FadeOut(ha), run_time=0.3)
        self.play(FadeOut(hot, shift=RIGHT * 1.6), run_time=0.3)
        f = M(r"W = \frac{8}{C}\sum_{i=1}^{k} s_i = \frac{8\cdot 4\cdot 2^{20}}{10^{10}}\ \mathrm{s} = 3.36\ \mathrm{ms}", size=44).move_to([-2.2, y - 2.2, 0])
        self.caption("It waited 3.36 ms. Its own transmission takes a few microseconds")
        self.play(Write(f), run_time=1.2)
        self.wait(2.4)

        # ---------- one queue per class ----------
        clock.clear_updaters(); cu.clear_updaters()
        summ = T("One queue:", size=30, color=MUTED)
        self.play(FadeOut(VGroup(lane, lane2, ql, wire, wl, clock, cu)), f.animate.scale(0.8).move_to([1.0, 3.1, 0]), run_time=0.7)
        summ.next_to(f, LEFT, buff=0.4)
        self.play(FadeIn(summ), run_time=0.3)
        yh, yc = 1.0, -0.75
        hq = VGroup(Line([-6.7, yh - 0.5, 0], [1.5, yh - 0.5, 0], color=HOT, stroke_width=4),
                    Line([-6.7, yh + 0.5, 0], [1.5, yh + 0.5, 0], color=HOT, stroke_width=4))
        cq = VGroup(Line([-6.7, yc - 0.58, 0], [1.5, yc - 0.58, 0], color=COLD, stroke_width=4),
                    Line([-6.7, yc + 0.58, 0], [1.5, yc + 0.58, 0], color=COLD, stroke_width=4))
        hlab = T("hot endpoint", size=30, color=HOT).move_to([-5.45, yh, 0])
        clab = T("cold endpoint", size=30, color=COLD).move_to([-5.4, yc, 0])
        dev = RoundedRectangle(width=3.0, height=3.2, corner_radius=0.12, stroke_color=EDGE, stroke_width=3,
                               fill_color=PANEL, fill_opacity=1).move_to([3.55, (yh + yc) / 2, 0])
        dl = P("one device,", "one cable", size=30, align="center").move_to(dev)
        j1 = Line([1.5, yh, 0], dev.get_left() + UP * 0.9, color=EDGE, stroke_width=4)
        j2 = Line([1.5, yc, 0], dev.get_left() + DOWN * 0.9, color=EDGE, stroke_width=4)
        out = Arrow(dev.get_right(), dev.get_right() + RIGHT * 1.5, color=EDGE, buff=0.05, stroke_width=6)
        c2 = [block(1.25, "cold", "1 MiB", h=0.78, size=26).move_to([0.75 - 1.38 * k, yc, 0]) for k in range(4)]
        h2 = block(0.5, "hot", h=0.66).move_to([-3.0, yh, 0])
        self.caption("One endpoint per class: the hot message has its own send queue")
        self.play(FadeIn(hq), FadeIn(cq), FadeIn(hlab), FadeIn(clab), FadeIn(dev), FadeIn(dl), Create(j1), Create(j2),
                  GrowArrow(out), *[FadeIn(b) for b in c2], run_time=0.9)
        self.play(FadeIn(h2, shift=RIGHT * 0.4), run_time=0.4)
        self.play(h2.animate.move_to([1.15, yh, 0]), run_time=0.8, rate_func=smooth)
        ok = T("follows from the design", size=30, color=OKC, weight=BOLD).move_to([-1.2, yh + 0.95, 0])
        self.play(FadeIn(ok), run_time=0.4)
        self.wait(1.6)
        self.caption("Below the endpoints the packets still meet. Experiment E3 measures that")
        qm = T("measured by E3", size=30, color=NAVY, weight=BOLD).next_to(dev, DOWN, buff=0.18)
        self.play(h2.animate.move_to(dev.get_left() + UP * 0.9 + LEFT * 0.14), c2[0].animate.move_to([1.0, yc, 0]),
                  FadeIn(qm), dev.animate.set_stroke(NAVY, 6), run_time=0.8)
        self.hold()
