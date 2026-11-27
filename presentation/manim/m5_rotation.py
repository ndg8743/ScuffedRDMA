"""M5: what the rotation does to a vector with a few large channels (example, d = 16)."""
from style import *

d = 16
rng = np.random.default_rng(3)
raw = rng.normal(0, 0.05, d)
raw[5] += 0.90; raw[11] += 0.32; raw[2] -= 0.26
u = raw / np.linalg.norm(raw)
H = np.array([[1.0]])
while H.shape[0] < d:
    H = np.block([[H, H], [H, -H]])
D = np.diag(rng.choice([-1.0, 1.0], d))
y = (H @ D @ u) / np.sqrt(d)
assert abs(np.linalg.norm(y) - 1) < 1e-9


class M5Rotation(Clip):
    def bars(self, vals, x0, base, sc, pitch=0.27, w=0.2, color=NAVY):
        g = VGroup()
        for i, v in enumerate(vals):
            h = max(abs(v) * sc, 0.03)
            r = Rectangle(width=w, height=h, stroke_width=0, fill_color=color, fill_opacity=1)
            r.move_to([x0 + i * pitch, base + np.sign(v) * h / 2, 0])
            g.add(r)
        return g

    def construct(self):
        base, sc, pitch = -0.35, 3.1, 0.27
        xl, xr = -6.45, 1.5
        width = (d - 1) * pitch
        axl = Line([xl - 0.25, base, 0], [xl + width + 0.25, base, 0], color=EDGE, stroke_width=3)
        axr = Line([xr - 0.25, base, 0], [xr + width + 0.25, base, 0], color=EDGE, stroke_width=3)
        bu = self.bars(u, xl, base, sc)
        tl = VGroup(M("u", size=54), T("before", size=30, color=MUTED)).arrange(RIGHT, buff=0.25, aligned_edge=DOWN).move_to([xl + width / 2, 3.2, 0])
        note = T("example, d = 16", size=28, color=MUTED).move_to([-0.5, 3.25, 0])
        su = T("length %.2f,  largest entry %.2f" % (np.linalg.norm(u), np.abs(u).max()), size=30, color=INK).move_to([xl + width / 2, -2.35, 0])
        self.add(axl, bu, tl, note, su)
        self.caption("A cache vector often has a few channels much larger than the rest", run_time=0)
        self.wait(2.4)

        self.caption("Rotate it: multiply by R")
        box = RoundedRectangle(width=2.75, height=1.25, corner_radius=0.12, stroke_color=NAVY, stroke_width=4, fill_color=PANEL, fill_opacity=1).move_to([-0.5, base + 1.3, 0])
        bl = M(r"R=\tfrac{1}{\sqrt d}HD", size=42, color=NAVY).move_to(box)
        a1 = Arrow([xl + width + 0.2, base + 1.3, 0], box.get_left(), buff=0.05, color=NAVY, stroke_width=6, max_tip_length_to_length_ratio=0.5)
        a2 = Arrow(box.get_right(), [xr - 0.2, base + 1.3, 0], buff=0.05, color=NAVY, stroke_width=6, max_tip_length_to_length_ratio=0.5)
        self.play(FadeIn(box), Write(bl), GrowArrow(a1), run_time=0.9)
        by = self.bars(y, xr, base, sc)
        tr = VGroup(M("y = Ru", size=54), T("after", size=30, color=MUTED)).arrange(RIGHT, buff=0.25, aligned_edge=DOWN).move_to([xr + width / 2, 3.2, 0])
        self.play(GrowArrow(a2), FadeIn(axr), FadeIn(tr), run_time=0.5)
        self.play(LaggedStart(*[TransformFromCopy(bu[i], by[i]) for i in range(d)], lag_ratio=0.05), run_time=2.2)
        self.caption("The same length, now spread over the coordinates")
        sy = T("length %.2f,  largest entry %.2f" % (np.linalg.norm(y), np.abs(y).max()), size=30, color=INK).move_to([xr + width / 2, -2.35, 0])
        self.play(FadeIn(sy), run_time=0.5)
        self.wait(2.0)

        self.caption("Each coordinate has mean 0 and variance 1/d: one set of levels fits all")
        s = 1 / np.sqrt(d) * sc
        up = DashedLine([xr - 0.25, base + s, 0], [xr + width + 0.25, base + s, 0], color=OKC, stroke_width=4, dash_length=0.14)
        dn = DashedLine([xr - 0.25, base - s, 0], [xr + width + 0.25, base - s, 0], color=OKC, stroke_width=4, dash_length=0.14)
        lb = M(r"\pm\tfrac{1}{\sqrt d}", size=42, color=OKC).next_to(up, RIGHT, buff=0.1).shift(DOWN * s)
        self.play(Create(up), Create(dn), FadeIn(lb), run_time=0.9)
        self.hold()
