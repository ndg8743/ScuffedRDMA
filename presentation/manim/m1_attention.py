"""M1: one attention layer as matrix products (example with 4 positions, d = 3)."""
from style import *
from grid import *

Q = np.array([[1, 0, 1], [0, 2, -1], [1, 1, 0], [2, -1, 1]], float)
K = np.array([[1, 1, 0], [0, 1, 1], [2, 0, -1], [1, -1, 2]], float)
V = np.array([[1, 0, 2], [0, 1, 1], [2, 1, 0], [1, 2, 1]], float)
S = Q @ K.T
d = Q.shape[1]
Z = S / np.sqrt(d)
mask = np.tril(np.ones_like(S))
E = np.exp(Z) * mask
A = E / E.sum(axis=1, keepdims=True)
O = A @ V


class M1Attention(Clip):
    def construct(self):
        C = 0.95
        y0 = 0.8
        gq = Grid(Q, cell=C).move_to([-4.2, y0, 0])
        gk = Grid(K, cell=C).move_to([-0.65, y0, 0])
        hq = head("Q", "queries", gq)
        hk = head("K", "keys", gk)
        pos = VGroup(*[T(str(i + 1), size=28, color=MUTED).next_to(gq.cell_at(i, 0), LEFT, buff=0.22)
                       for i in range(4)])
        posl = T("position", size=28, color=MUTED).rotate(PI / 2).next_to(pos, LEFT, buff=0.14)
        note = T("example with 4 positions and d = 3", size=30, color=MUTED).move_to([0, -2.2, 0])
        self.add(gq, gk, hq, hk, pos, posl, note)
        self.caption("Each position has a query row and a key row", run_time=0)
        self.wait(2.0)

        gs = Grid(S, cell=C).move_to([3.7, y0, 0])
        hs = VGroup(M(r"S = QK^{\top}", size=48), T("scores", size=28, color=MUTED)).arrange(RIGHT, buff=0.22, aligned_edge=DOWN)
        hs.next_to(gs, UP, buff=0.25)
        self.play(FadeIn(gs.cells), FadeIn(hs), FadeOut(note), run_time=0.7)
        self.caption("Score (i, j) is the dot product of query i with key j")
        i, j = 2, 1
        fq = frame(gq.row(i)); fk = frame(gk.row(j)); fs = frame(gs.cell_at(i, j))
        terms = " + ".join("(%d)(%d)" % (Q[i, t], K[j, t]) for t in range(d))
        read = M(r"q_{3}\cdot k_{2} = " + terms + " = %d" % S[i, j], size=46, color=NAVY).move_to([0, -2.2, 0])
        self.play(Create(fq), Create(fk), run_time=0.6)
        self.play(Write(read), Create(fs), run_time=1.3)
        self.play(FadeIn(gs.num_at(i, j), scale=1.6), run_time=0.5)
        self.wait(0.9)
        i2, j2 = 3, 3
        terms2 = " + ".join("(%d)(%d)" % (Q[i2, t], K[j2, t]) for t in range(d))
        read2 = M(r"q_{4}\cdot k_{4} = " + terms2 + " = %d" % S[i2, j2], size=46, color=NAVY).move_to(read)
        self.play(fq.animate.move_to(gq.row(i2)), fk.animate.move_to(gk.row(j2)),
                  fs.animate.move_to(gs.cell_at(i2, j2)), FadeOut(read), FadeIn(read2), run_time=0.9)
        self.play(FadeIn(gs.num_at(i2, j2), scale=1.6), run_time=0.4)
        self.wait(0.6)
        rest = [gs.num_at(a, b) for a in range(4) for b in range(4) if (a, b) not in ((i, j), (i2, j2))]
        self.play(LaggedStart(*[FadeIn(n, shift=0.1 * UP) for n in rest], lag_ratio=0.06),
                  FadeOut(fq), FadeOut(fk), FadeOut(fs), FadeOut(read2), run_time=1.3)
        self.wait(0.6)

        self.caption("Causal mask: position i reads positions 1 to i")
        upper = [(a, b) for a in range(4) for b in range(4) if b > a]
        infs = VGroup(*[M(r"-\infty", size=38, color=MUTED).move_to(gs.cell_at(a, b)) for a, b in upper])
        self.play(*[gs.cell_at(a, b).animate.set_fill(LIGHT, 1) for a, b in upper],
                  *[FadeOut(gs.num_at(a, b)) for a, b in upper], FadeIn(infs), run_time=0.9)
        self.wait(1.4)

        self.caption("Divide by √d, then softmax each row: weights that sum to 1")
        ga = Grid(A, cell=C, places=2, size=34).move_to([-4.25, y0, 0])
        for a in range(4):
            for b in range(4):
                if b > a:
                    ga.cell_at(a, b).set_fill(LIGHT, 1)
                    ga.num_at(a, b).set_opacity(0)
                else:
                    ga.cell_at(a, b).set_fill(AMBER, 0.12 + 0.88 * A[a, b])
        ha = M(r"A = \mathrm{softmax}\!\left(S/\sqrt{d}\right)", size=42).next_to(ga, UP, buff=0.25)
        self.play(FadeOut(gq), FadeOut(gk), FadeOut(hq), FadeOut(hk), FadeOut(pos), FadeOut(posl), run_time=0.5)
        low = [gs.num_at(a, b) for a in range(4) for b in range(4) if b <= a]
        self.play(ReplacementTransform(gs.cells, ga.cells), FadeOut(VGroup(*low)), FadeOut(infs),
                  ReplacementTransform(hs, ha), run_time=1.1)
        self.play(LaggedStart(*[FadeIn(ga.num_at(a, b)) for a in range(4) for b in range(4) if b <= a],
                              lag_ratio=0.05), run_time=0.9)
        sums = VGroup(*[M(r"\Sigma = 1", size=38, color=MUTED).next_to(ga.cell_at(a, 3), RIGHT, buff=0.22)
                        for a in range(4)])
        self.play(FadeIn(sums, shift=0.1 * RIGHT), run_time=0.5)
        self.wait(1.6)

        self.caption("Each output row is a weighted mix of the value rows")
        gv = Grid(V, cell=C).move_to([0.35, y0, 0])
        hv = head("V", "values", gv)
        go = Grid(O, cell=C, places=2, size=34).move_to([4.5, y0, 0])
        ho = head("AV", "output", go)
        times = M(r"\times", size=48).move_to([(ga.get_right()[0] + gv.get_left()[0]) / 2, y0, 0])
        eq = M("=", size=48).move_to([(gv.get_right()[0] + go.get_left()[0]) / 2, y0, 0])
        self.play(FadeOut(sums), run_time=0.3)
        self.play(FadeIn(gv), FadeIn(hv), FadeIn(times), FadeIn(eq), FadeIn(go.cells), FadeIn(ho), run_time=0.8)
        r = 3
        fa = frame(ga.row(r)); fo = frame(go.row(r))
        mix = " + ".join("%.2f\\,v_{%d}" % (A[r, t], t + 1) for t in range(4))
        read3 = M(r"o_{4} = " + mix, size=44, color=NAVY).move_to([0, -2.2, 0])
        self.play(Create(fa), Create(fo), Write(read3), run_time=1.2)
        self.play(LaggedStart(*[FadeIn(n, scale=1.4) for n in go.row_nums(r)], lag_ratio=0.15), run_time=0.7)
        self.wait(1.0)
        others = [go.num_at(a, b) for a in range(3) for b in range(3)]
        self.play(LaggedStart(*[FadeIn(n) for n in others], lag_ratio=0.05), FadeOut(fa), FadeOut(fo),
                  FadeOut(read3), run_time=1.0)
        final = M(r"\mathrm{Attention}(Q,K,V)=\mathrm{softmax}\!\left(\frac{QK^{\top}}{\sqrt{d}}\right)V",
                  size=46, color=NAVY).move_to([0, -2.2, 0])
        self.play(Write(final), run_time=1.4)
        self.hold()
