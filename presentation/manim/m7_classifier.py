"""M7: the learned classifier as a matrix times a feature vector, then a softmax over the three states."""
from style import *

FEATS = ["t", "p", "e", "tp", "te", r"\cdots", "1"]
VALS = ["t", "0", "1", "0", "t", r"\vdots", "1"]       # a transfer during decode: p = 0, e = 1
rng = np.random.default_rng(5)
Wv = rng.uniform(-1, 1, (3, 7))
Wv[2, 4] = -1.0; Wv[2, 2] = 0.9; Wv[0, 4] = 0.9; Wv[0, 2] = -0.8      # only a picture: no values are read from it
STATES = [("Cold", COLD, 0.10), ("Warm", MUTED, 0.22), ("Hot", HOT, 0.68)]   # bar lengths are illustrative


class M7Classifier(Clip):
    def construct(self):
        c = 0.72
        wx, wy = -3.2, 0.9
        cells = VGroup()
        for i in range(3):
            for j in range(7):
                v = Wv[i, j]
                sq = Square(c, stroke_color=BG, stroke_width=3, fill_color=NAVY if v > 0 else HOTF, fill_opacity=0.18 + 0.72 * abs(v))
                sq.move_to([wx + (j - 3) * c, wy - (i - 1) * c, 0])
                cells.add(sq)
        wb = SurroundingRectangle(cells, color=INK, buff=0.03, stroke_width=2.5)
        heads = VGroup(*[M(f, size=36, color=MUTED).move_to([wx + (j - 3) * c, wy + 1.5 * c + 0.28, 0]) for j, f in enumerate(FEATS)])
        rows = VGroup(*[T(s, size=30, color=col).move_to([wx - 3.5 * c - 0.2, wy - (i - 1) * c, 0]).align_to([wx - 3.5 * c - 0.2, 0, 0], RIGHT)
                        for i, (s, col, _) in enumerate(STATES)])
        wl = VGroup(M(r"W_{s}", size=48), T("weights (illustrative)", size=28, color=MUTED)).arrange(RIGHT, buff=0.25, aligned_edge=DOWN)
        wl.move_to([wx, wy + 1.5 * c + 1.0, 0])
        # feature column
        fx = 0.6
        hh = 0.58
        fcells = VGroup(); fvals = VGroup()
        for j in range(7):
            sq = Square(c, stroke_color=EDGE, stroke_width=2.5, fill_color=BG, fill_opacity=1).move_to([fx, wy + (3 - j) * hh, 0])
            sq.stretch_to_fit_height(hh)
            fcells.add(sq); fvals.add(M(VALS[j], size=38).move_to(sq))
        fl = M(r"\phi(x)", size=48).next_to(fcells, UP, buff=0.22)
        fn = VGroup(*[M(f, size=34, color=MUTED).next_to(fcells[j], RIGHT, buff=0.16) for j, f in enumerate(FEATS)])
        times = M(r"\times", size=48).move_to([(wx + 3.5 * c + fx - c / 2) / 2, wy, 0])
        note = T("a transfer during decode: p = 0, e = 1", size=28, color=MUTED).move_to([0, -2.55, 0])
        self.add(cells, wb, heads, rows, wl, fcells, fvals, fl, fn, times, note)
        self.caption("Features of one transfer, and one row of weights for each next state", run_time=0)
        self.wait(2.6)

        self.caption("Each row times the features gives one score")
        eq = M("=", size=48).move_to([2.2, wy, 0])
        bx = 2.75
        bars = VGroup(); labs = VGroup()
        scores = [0.9, 1.5, 2.6]
        self.play(FadeIn(eq), run_time=0.3)
        for i, (s, col, _) in enumerate(STATES):
            y = wy - (i - 1) * c
            rowf = SurroundingRectangle(VGroup(*[cells[i * 7 + j] for j in range(7)]), color=NAVY, buff=0.0, stroke_width=7)
            colf = SurroundingRectangle(fcells, color=NAVY, buff=0.0, stroke_width=7)
            b = Rectangle(width=scores[i], height=c * 0.62, stroke_width=0, fill_color=col, fill_opacity=1).move_to([bx + scores[i] / 2, y, 0])
            self.play(Create(rowf), Create(colf), run_time=0.45)
            self.play(GrowFromEdge(b, LEFT), run_time=0.55)
            self.play(FadeOut(rowf), FadeOut(colf), run_time=0.25)
            bars.add(b)
        sl = T("scores", size=28, color=MUTED).move_to([bx + 0.6, wy + 1.5 * c + 0.28, 0])
        self.play(FadeIn(sl), run_time=0.3)
        self.wait(1.0)

        self.caption("A softmax turns the three scores into probabilities")
        full = 3.6
        targets = [Rectangle(width=full * p, height=c * 0.62, stroke_width=0, fill_color=col, fill_opacity=1).move_to([bx + full * p / 2, wy - (i - 1) * c, 0])
                   for i, (s, col, p) in enumerate(STATES)]
        sl2 = T("probabilities, sum 1", size=28, color=MUTED).move_to(sl).align_to(sl, LEFT)
        self.play(*[Transform(bars[i], targets[i]) for i in range(3)], FadeOut(sl), FadeIn(sl2), run_time=1.0)
        f = M(r"P(s'\mid s,x)=\frac{\exp\!\big(W_{s,s'}\cdot\phi(x)\big)}{\sum_{r}\exp\!\big(W_{s,r}\cdot\phi(x)\big)}", size=42, color=NAVY).move_to([0, -2.3, 0])
        self.play(FadeOut(note), Write(f), run_time=1.3)
        self.wait(1.2)

        self.caption("The most probable state decides the endpoint")
        win = SurroundingRectangle(bars[2], color=INK, buff=0.1, stroke_width=6, corner_radius=0.08)
        wt = T("hot endpoint", size=30, color=HOT, weight=BOLD).next_to(bars[2], DOWN, buff=0.3).align_to(bars[2], LEFT)
        self.play(Create(win), FadeIn(wt), run_time=0.8)
        self.hold()
