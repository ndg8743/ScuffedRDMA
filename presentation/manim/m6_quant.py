"""M6: eight Lloyd-Max levels, the residual, the 256-bit sign sketch, and the packed 64 bytes."""
from style import *

LEVELS = [-2.118, -1.338, -0.764, -0.257, 0.233, 0.738, 1.316, 2.097]   # d = 64, b = 3, from the code, in units of 1/sqrt(d)
rng = np.random.default_rng(11)
SAMPLES = np.clip(rng.normal(0, 1, 14), -2.6, 2.6)
BITS = rng.choice([0, 1], size=(16, 16))


class M6Quantize(Clip):
    def construct(self):
        ax_y, sx, bh = 1.55, 2.12, 1.55
        X = lambda v: v * sx
        axis = Line([X(-3.05), ax_y, 0], [X(3.05), ax_y, 0], color=INK, stroke_width=3)
        bell = VMobject(stroke_color=MUTED, stroke_width=3, fill_color=LIGHT, fill_opacity=0.8)
        vs = np.linspace(-3.05, 3.05, 120)
        pts = [[X(-3.05), ax_y, 0]] + [[X(v), ax_y + bh * np.exp(-v * v / 2), 0] for v in vs] + [[X(3.05), ax_y, 0]]
        bell.set_points_as_corners(pts)
        note = T("d = 64, 3 bits per coordinate. Levels from the code, in units of 1/√d", size=28, color=MUTED).move_to([0, 3.62, 0])
        self.add(bell, axis, note)
        self.caption("After the rotation the coordinates follow the same bell curve", run_time=0)
        self.wait(2.2)

        self.caption("Eight Lloyd-Max levels: 3 bits name the level")
        ticks, vals, codes = VGroup(), VGroup(), VGroup()
        for k, v in enumerate(LEVELS):
            ticks.add(Line([X(v), ax_y - 0.16, 0], [X(v), ax_y + 0.55, 0], color=NAVY, stroke_width=8))
            vals.add(DecimalNumber(v, num_decimal_places=2, font_size=36, color=NAVY).move_to([X(v), ax_y - 0.5, 0]))
            codes.add(T(format(k, "03b"), size=28, color=INK, font=MONO).move_to([X(v), ax_y - 1.0, 0]))
        mids = [(LEVELS[k] + LEVELS[k + 1]) / 2 for k in range(7)]
        cuts = VGroup(*[DashedLine([X(m), ax_y, 0], [X(m), ax_y + bh * np.exp(-m * m / 2), 0], color=EDGE, stroke_width=2.5, dash_length=0.08) for m in mids])
        self.play(LaggedStart(*[AnimationGroup(Create(ticks[k]), FadeIn(vals[k]), FadeIn(codes[k])) for k in range(8)], lag_ratio=0.12),
                  FadeIn(cuts), run_time=1.8)
        self.wait(1.2)

        self.caption("Each coordinate is rounded to the nearest level")
        yd = ax_y + 0.26
        dots = VGroup(*[Dot([X(v), yd, 0], radius=0.11, color=HOTF).set_stroke(INK, 1.5) for v in SAMPLES])
        self.play(LaggedStart(*[FadeIn(dt, shift=DOWN * 1.2) for dt in dots], lag_ratio=0.06), run_time=1.1)
        self.wait(0.4)
        near = [min(LEVELS, key=lambda L: abs(L - v)) for v in SAMPLES]
        segs = VGroup(*[Line([X(v), yd, 0], [X(n), yd, 0], color=NAVY, stroke_width=8) for v, n in zip(SAMPLES, near)])
        self.play(*[dt.animate.move_to([X(n), yd, 0]) for dt, n in zip(dots, near)], FadeIn(segs), run_time=1.3)
        self.wait(1.2)

        self.caption("The rounding error is the residual. Keep its length and 256 random signs")
        cell, pit = 0.118, 0.142
        grid = VGroup()
        for i in range(16):
            for j in range(16):
                sq = Square(cell, stroke_color=SPILL, stroke_width=1.2, fill_color=SPILL, fill_opacity=1.0 if BITS[i, j] else 0.0)
                sq.move_to([-6.55 + j * pit, -0.4 - i * pit, 0])
                grid.add(sq)
        gl = P("256 signs of", "random", "projections", size=28, color=SPILL).next_to(grid, RIGHT, buff=0.2)
        self.play(LaggedStart(*[FadeIn(sq) for sq in grid], lag_ratio=0.004), FadeIn(gl), run_time=1.6)
        self.wait(1.2)

        self.caption("Packed: 64 bytes for a vector that takes 128 in 16-bit")
        ux = 4.2 / 128.0
        x0 = 0.75
        y1, y2 = -0.8, -1.62
        full = Rectangle(width=128 * ux, height=0.5, stroke_color=MUTED, stroke_width=2.5, fill_color=LIGHT, fill_opacity=1)
        full.move_to([x0 + 64 * ux, y1, 0])
        fl = T("16-bit", size=30, color=INK).next_to(full, LEFT, buff=0.25)
        fr = T("128 bytes", size=30, color=INK).next_to(full, RIGHT, buff=0.2)
        parts = [(4, INK), (4, MUTED), (24, NAVY), (32, SPILL)]
        segs2 = VGroup(); x = x0
        for n, c in parts:
            r = Rectangle(width=n * ux, height=0.5, stroke_color=BG, stroke_width=3, fill_color=c, fill_opacity=1)
            r.move_to([x + n * ux / 2, y2, 0]); segs2.add(r); x += n * ux
        pl = T("packed", size=30, color=INK).next_to(segs2, LEFT, buff=0.25)
        pr = T("64 bytes", size=32, color=NAVY, weight=BOLD).next_to(segs2, RIGHT, buff=0.2)
        legend = VGroup(T("lengths 4 + 4", size=28, color=INK), T("codes 24", size=28, color=NAVY),
                        T("sign sketch 32", size=28, color=SPILL)).arrange(RIGHT, buff=0.45)
        legend.move_to([0, -2.42, 0]).align_to(pl, LEFT)
        self.play(FadeIn(full), FadeIn(fl), FadeIn(fr), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(r, shift=0.15 * UP) for r in segs2], lag_ratio=0.2), FadeIn(pl), run_time=1.0)
        self.play(FadeIn(pr), FadeIn(legend), run_time=0.7)
        self.hold()
