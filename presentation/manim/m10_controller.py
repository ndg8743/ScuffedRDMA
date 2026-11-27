"""M10: where the implemented switching rule and the rule that follows from the model disagree."""
from style import *


class M10Controller(Clip):
    def construct(self):
        ax = Axes(x_range=[0, 10, 2], y_range=[0, 10, 2], x_length=5.4, y_length=5.0, tips=False,
                  axis_config={"color": INK, "stroke_width": 3, "include_ticks": False}).move_to([-3.25, 0.45, 0])
        xl = M(r"q_H", size=44).next_to(ax.x_axis, RIGHT, buff=0.15)
        xw = T("hot backlog", size=28, color=MUTED).next_to(ax.x_axis, DOWN, buff=0.15)
        yl = M(r"q_C", size=44).move_to(ax.c2p(0, 10)).shift(LEFT * 0.5)
        yw = T("cold backlog", size=28, color=MUTED).rotate(PI / 2).next_to(ax.y_axis, LEFT, buff=0.15).shift(DOWN * 0.4)
        P0 = ax.c2p(0, 0)
        note = T("defaults: α = 2, β = 1, μH = 10,000, μC = 2,000", size=26, color=MUTED).move_to([3.4, -2.6, 0])
        self.add(ax, xl, xw, yl, yw, note)
        self.caption("A new transfer arrives. Which path should it join?", run_time=0)
        self.wait(2.2)

        # implemented rule: cold when q_C < 10 q_H
        self.caption("Implemented rule: cold once the hot backlog passes a tenth of the cold one")
        cold1 = Polygon(P0, ax.c2p(1, 10), ax.c2p(10, 10), ax.c2p(10, 0), stroke_width=0, fill_color=COLDF, fill_opacity=1).set_z_index(-2)
        hot1 = Polygon(P0, ax.c2p(1, 10), ax.c2p(0, 10), stroke_width=0, fill_color=HOTF, fill_opacity=0.55).set_z_index(-2)
        l1 = Line(P0, ax.c2p(1, 10), color=INK, stroke_width=5)
        f1 = M(r"\alpha q_H\mu_H > \beta q_C\mu_C", size=40).move_to([3.7, 1.15, 0])
        f1b = VGroup(T("implemented: send cold when", size=28, color=MUTED), f1, M(r"q_H > q_C/10", size=44, color=COLD)).arrange(DOWN, buff=0.18).move_to([3.9, 0.85, 0])
        tc = T("cold", size=34, color=COLD, weight=BOLD).move_to(ax.c2p(6.3, 5.2))
        th = T("hot", size=28, color=HOT, weight=BOLD).move_to(ax.c2p(0.9, 10.6))
        self.play(Create(l1), FadeIn(cold1), FadeIn(hot1), FadeIn(f1b), FadeIn(tc), FadeIn(th), run_time=1.2)
        self.wait(2.2)

        # consistent rule: cold when q_C < 0.4 q_H
        self.caption("Rule that follows from the model: cold above two and a half times")
        cold2 = Polygon(P0, ax.c2p(10, 4), ax.c2p(10, 0), stroke_width=0, fill_color=COLDF, fill_opacity=1).set_z_index(-2)
        wedge = Polygon(P0, ax.c2p(1, 10), ax.c2p(10, 10), ax.c2p(10, 4), stroke_width=0, fill_color=LIGHT, fill_opacity=1).set_z_index(-2)
        l2 = Line(P0, ax.c2p(10, 4), color=OKC, stroke_width=6)
        f2 = VGroup(T("consistent: send cold when", size=28, color=MUTED), M(r"\frac{\alpha q_H}{\mu_H} > \frac{\beta q_C}{\mu_C}", size=40),
                    M(r"q_H > 2.5\,q_C", size=44, color=OKC)).arrange(DOWN, buff=0.18).move_to([3.9, 0.9, 0])
        self.play(f1b.animate.scale(0.8).move_to([3.9, 2.75, 0]), run_time=0.5)
        self.play(Create(l2), FadeOut(cold1), FadeIn(cold2), FadeIn(wedge), FadeIn(f2), tc.animate.move_to(ax.c2p(7.9, 1.3)), run_time=1.2)
        tw = P("the two rules", "disagree here", size=30, color=INK, align="center").move_to(ax.c2p(6.2, 6.6))
        self.play(FadeIn(tw), run_time=0.5)
        self.wait(2.0)

        self.caption("The implemented rule leaves the hot path at 25 times less hot backlog")
        k = VGroup(T("factor", size=30, color=NAVY), T("25", size=64, color=NAVY, weight=BOLD)).arrange(RIGHT, buff=0.25, aligned_edge=DOWN).move_to([3.9, -1.5, 0])
        self.play(FadeIn(k, scale=1.2), run_time=0.7)
        self.hold()
