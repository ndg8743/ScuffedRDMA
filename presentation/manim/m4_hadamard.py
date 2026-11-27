"""M4: the Hadamard matrix by doubling, rows orthogonal, the rotation R."""
from style import *

PLUS, MINUS = NAVY, LIGHT
CA, CB = HOTF, COLDL


def had(n):
    H = np.array([[1.0]])
    while H.shape[0] < n:
        H = np.block([[H, H], [H, -H]])
    return H


class M4Hadamard(Clip):
    S = 4.7
    CX, CY = -3.45, 0.5

    def cells(self, n):
        H = had(n); c = self.S / n; out = {}
        for i in range(n):
            for j in range(n):
                sq = Square(c, stroke_color=BG, stroke_width=4 if n < 8 else 3, fill_opacity=1,
                            fill_color=PLUS if H[i, j] > 0 else MINUS)
                sq.move_to([self.CX - self.S / 2 + c * (j + 0.5), self.CY + self.S / 2 - c * (i + 0.5), 0])
                out[(i, j)] = sq
        return out

    def construct(self):
        rule = M(r"H_1=(1),\quad H_{2n}=\begin{pmatrix}H_n & H_n\\ H_n & -H_n\end{pmatrix}", size=44).move_to([3.35, 2.75, 0])
        leg = VGroup(Square(0.36, stroke_color=INK, stroke_width=1.5, fill_color=PLUS, fill_opacity=1), M("+1", size=40),
                     Square(0.36, stroke_color=INK, stroke_width=1.5, fill_color=MINUS, fill_opacity=1), M("-1", size=40))
        leg.arrange(RIGHT, buff=0.2); leg[2].shift(RIGHT * 0.4); leg[3].shift(RIGHT * 0.4)
        leg.move_to([self.CX, self.CY - self.S / 2 - 0.45, 0])
        border = Square(self.S + 0.1, stroke_color=INK, stroke_width=2.5).move_to([self.CX, self.CY, 0])
        cur = self.cells(1)
        name = M("H_1", size=54).move_to([self.CX - self.S / 2 - 0.8, self.CY, 0])
        self.add(border, cur[(0, 0)], name, leg, rule)
        self.caption("Start from the 1 by 1 matrix (1)", run_time=0)
        self.wait(1.8)
        n = 1
        caps = {2: "Double it: three copies, and a fourth with every sign flipped", 4: "Repeat: 4 by 4", 8: "Repeat: 8 by 8"}
        while n < 8:
            m = 2 * n
            self.caption(caps[m])
            G = self.cells(m)
            fast = 1.0 if m == 2 else 0.8
            self.play(*[Transform(cur[(i, j)], G[(i, j)]) for i in range(n) for j in range(n)], run_time=0.7 * fast)
            new = {}
            anims = []
            for i in range(n):
                for j in range(n):
                    for (di, dj) in ((0, n), (n, 0), (n, n)):
                        t = G[(i + di, j + dj)].copy()
                        if (di, dj) == (n, n):
                            t.set_fill(cur[(i, j)].get_fill_color())
                        new[(i + di, j + dj)] = t
                        anims.append(TransformFromCopy(cur[(i, j)], t))
            self.play(*anims, run_time=0.9 * fast)
            flip = [new[(i + n, j + n)].animate.set_fill(G[(i + n, j + n)].get_fill_color()) for i in range(n) for j in range(n)]
            nn = M("H_{%d}" % m, size=54).move_to(name)
            self.play(*flip, Transform(name, nn), run_time=0.7 * fast)
            cur.update(new)
            n = m
            self.wait(0.7)
        self.wait(0.6)

        self.caption("Any two rows agree in half the places and differ in the other half")
        H = had(8); a, b = 2, 5
        fa = SurroundingRectangle(VGroup(*[cur[(a, j)] for j in range(8)]), color=CA, buff=0.0, stroke_width=8)
        fb = SurroundingRectangle(VGroup(*[cur[(b, j)] for j in range(8)]), color=CB, buff=0.0, stroke_width=8)
        k = 0.52

        def strip(vals, y):
            g = VGroup(*[Square(k, stroke_color=BG, stroke_width=3, fill_opacity=1, fill_color=PLUS if v > 0 else MINUS)
                         for v in vals]).arrange(RIGHT, buff=0)
            g.move_to([3.85, y, 0])
            return g

        sa, sb = strip(H[a], 1.3), strip(H[b], 0.68)
        sp = strip(H[a] * H[b], -0.2)
        la = M(r"h_3", size=42, color=HOT).next_to(sa, LEFT, buff=0.25)
        lb = M(r"h_6", size=42, color=COLD).next_to(sb, LEFT, buff=0.25)
        lp = T("product", size=28, color=MUTED).next_to(sp, LEFT, buff=0.25)
        self.play(Create(fa), Create(fb), run_time=0.5)
        self.play(TransformFromCopy(VGroup(*[cur[(a, j)] for j in range(8)]), sa),
                  TransformFromCopy(VGroup(*[cur[(b, j)] for j in range(8)]), sb), FadeIn(la), FadeIn(lb), run_time=0.9)
        self.play(FadeIn(sp, shift=0.2 * DOWN), FadeIn(lp), run_time=0.6)
        dot = M(r"h_3\cdot h_6 = 4 - 4 = 0", size=44, color=NAVY).move_to([3.4, -1.0, 0])
        self.play(Write(dot), run_time=0.9)
        self.wait(1.8)

        self.caption("Scaled by 1/√d, with random sign flips D, it is a rotation")
        f1 = M(r"H_d H_d^{\top} = d\,I", size=44).move_to([3.4, -1.85, 0])
        f2 = M(r"R=\tfrac{1}{\sqrt{d}}\,H_d D \;\Rightarrow\; RR^{\top}=I", size=44, color=OKC).move_to([3.4, -2.6, 0])
        self.play(FadeOut(fa), FadeOut(fb), Write(f1), run_time=0.9)
        self.play(Write(f2), run_time=1.1)
        self.hold()
