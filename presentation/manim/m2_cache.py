"""M2a: the cache is a set of rows computed once. M2b: how large it is."""
from style import *
from grid import *

rng = np.random.default_rng(7)


def vec_row(n=6, cell=0.62, color=COLD, vals=None):
    vals = rng.uniform(0.22, 1.0, n) if vals is None else vals
    g = VGroup(*[Square(cell, stroke_color=BG, stroke_width=3, fill_color=color, fill_opacity=float(v))
                 for v in vals]).arrange(RIGHT, buff=0)
    return g


class M2aCacheRows(Clip):
    def construct(self):
        cell = 0.62
        pitch = cell + 0.06
        x_k, x_v, y_top = -2.1, 2.3, 2.15
        hk = VGroup(M("K", size=50), T("keys", size=30, color=MUTED)).arrange(RIGHT, buff=0.2, aligned_edge=DOWN)
        hv = VGroup(M("V", size=50), T("values", size=30, color=MUTED)).arrange(RIGHT, buff=0.2, aligned_edge=DOWN)
        hk.move_to([x_k, y_top + 0.85, 0]); hv.move_to([x_v, y_top + 0.85, 0])
        rows_k, rows_v, tags = [], [], []
        for i in range(4):
            y = y_top - i * pitch
            rk = vec_row(cell=cell).move_to([x_k, y, 0]); rv = vec_row(cell=cell).move_to([x_v, y, 0])
            tg = M("t_{%d}" % (i + 1), size=40, color=INK).next_to(rk, LEFT, buff=0.3)
            rows_k.append(rk); rows_v.append(rv); tags.append(tg)
        self.add(hk, hv, *rows_k, *rows_v, *tags)
        self.caption("Prefill: one pass gives each prompt token a key row and a value row", run_time=0)
        self.wait(2.4)

        self.caption("Decode: each new token adds one row. Earlier rows stay the same")
        br = lab = None
        for i in range(4, 7):
            y = y_top - i * pitch
            rk = vec_row(cell=cell, color=HOTF).move_to([x_k, y, 0]); rv = vec_row(cell=cell, color=HOTF).move_to([x_v, y, 0])
            tg = M("t_{%d}" % (i + 1), size=40, color=INK).next_to(rk, LEFT, buff=0.3)
            nbr = Brace(VGroup(*rows_v), RIGHT, buff=0.15, color=MUTED)
            scan = SurroundingRectangle(VGroup(*rows_k), color=NAVY, buff=0.04, stroke_width=6, corner_radius=0.05)
            q = VGroup(M("q_{%d}" % (i + 1), size=40, color=INK), vec_row(cell=0.2, color=HOTF)).arrange(RIGHT, buff=0.15)
            q.move_to([-6.0, VGroup(*rows_k).get_center()[1], 0])
            ar = Arrow(q.get_right(), [VGroup(*tags).get_left()[0] - 0.05, q.get_center()[1], 0], buff=0.08, color=NAVY,
                       stroke_width=6, max_tip_length_to_length_ratio=0.5)
            fast = 0.8 if i == 4 else 0.5
            anims = [FadeIn(q, shift=0.2 * RIGHT), GrowArrow(ar), Create(scan)]
            if br is None:
                br = nbr
                lab = P("computed", "once, reused", size=30, color=MUTED)
                lab.next_to(br, RIGHT, buff=0.15)
                anims += [FadeIn(br), FadeIn(lab)]
            else:
                anims += [Transform(br, nbr), lab.animate.next_to(nbr, RIGHT, buff=0.15)]
            self.play(*anims, run_time=fast)
            self.wait(0.3 if i == 4 else 0.1)
            self.play(FadeIn(rk, shift=0.2 * UP), FadeIn(rv, shift=0.2 * UP), FadeIn(tg), FadeOut(scan), FadeOut(q), FadeOut(ar),
                      run_time=fast)
            self.play(*[sq.animate.set_fill(COLD, float(v)) for sq, v in zip(rk, rng.uniform(0.22, 1.0, 6))],
                      *[sq.animate.set_fill(COLD, float(v)) for sq, v in zip(rv, rng.uniform(0.22, 1.0, 6))],
                      run_time=0.35)
            rows_k.append(rk); rows_v.append(rv); tags.append(tg)
        self.wait(1.0)

        self.caption("So the rows can be built on one machine and used on another")
        cache = VGroup(*rows_k, *rows_v)
        s1 = RoundedRectangle(width=4.7, height=4.1, corner_radius=0.15, stroke_color=EDGE, stroke_width=3, fill_color=PANEL, fill_opacity=1).move_to([-4.35, 0.3, 0])
        s2 = s1.copy().move_to([4.35, 0.3, 0])
        for s in (s1, s2):
            s.set_z_index(-5)
        l1 = T("prefill server", size=34, color=INK).next_to(s1, UP, buff=0.18)
        l2 = T("decode server", size=34, color=INK).next_to(s2, UP, buff=0.18)
        link = Line(s1.get_right(), s2.get_left(), color=EDGE, stroke_width=8).set_z_index(-6)
        ll = T("one link", size=30, color=MUTED).next_to(link, DOWN, buff=0.2)
        small = cache.copy().scale(0.47).move_to(s1.get_center() + UP * 0.3)
        self.play(FadeOut(VGroup(*tags, hk, hv, br, lab)), FadeIn(s1), FadeIn(s2), FadeIn(l1), FadeIn(l2),
                  Create(link), FadeIn(ll), Transform(cache, small), run_time=1.2)
        tag = T("key-value cache", size=30, color=COLD).next_to(cache, DOWN, buff=0.2)
        built = T("builds the rows", size=28, color=MUTED).move_to(s1.get_bottom() + UP * 0.38)
        used = T("uses them", size=28, color=MUTED).move_to(s2.get_bottom() + UP * 0.38)
        self.play(FadeIn(tag), FadeIn(built), run_time=0.4)
        self.wait(0.4)
        pack = VGroup(cache, tag)
        self.add(pack)
        self.play(pack.animate.shift(RIGHT * 8.7), run_time=2.4, rate_func=smooth)
        self.play(FadeIn(used), run_time=0.4)
        self.hold()


class M2bCacheSize(Clip):
    def construct(self):
        note = T("Granite 3.3 2B: 8 key-value heads, 64 dimensions, 16-bit values, 40 layers", size=28, color=MUTED).move_to([0, 3.6, 0])
        x0, y0, w1, h1, dx, dy = -6.6, -0.7, 0.5, 1.45, 0.03, 0.03

        def slab(k, w):
            s = Rectangle(width=w, height=h1, stroke_color=COLD, stroke_width=2, fill_color=COLDF, fill_opacity=1)
            s.move_to([x0 + w / 2 + dx * k, y0 + h1 / 2 + dy * k, 0])
            s.set_z_index(-k)
            return s

        first = slab(0, w1)
        f1 = M(r"2\cdot h\cdot d\cdot w = 2\cdot 8\cdot 64\cdot 2 = 2{,}048\ \text{bytes}", size=44).move_to([0, 2.75, 0])
        xa, xb = -0.3, 4.3

        def line(words, value, y, size=46):
            a = T(words, size=30, color=MUTED); b = T(value, size=size, color=COLD, weight=BOLD)
            a.move_to([0, y, 0]).align_to([xa, 0, 0], LEFT); b.move_to([0, y, 0]).align_to([xb, 0, 0], LEFT)
            return VGroup(a, b)

        r1 = line("one token, one layer", "2 KiB", 1.65)
        self.add(note, first, f1, r1)
        self.caption("One token in one layer: a key row and a value row for each head", run_time=0)
        self.wait(2.4)

        self.caption("Forty layers each keep their own rows")
        rest = [slab(k, w1) for k in range(1, 40)]
        self.play(LaggedStart(*[FadeIn(s) for s in rest], lag_ratio=0.04), run_time=1.6)
        slabs = [first] + rest
        lay = T("40 layers", size=28, color=MUTED).move_to([x0 + 40 * dx + 1.0, y0 + h1 + 40 * dy + 0.28, 0])
        r2 = line("one token, 40 layers", "80 KiB", 0.8)
        self.play(FadeIn(r2, shift=0.15 * UP), FadeIn(lay), run_time=0.5)
        self.wait(1.2)

        self.caption("A prompt of 2,048 tokens multiplies that by 2,048")
        W = 3.6
        self.play(*[Transform(s, slab(k, W)) for k, s in enumerate(slabs)], run_time=1.4)
        tok = T("2,048 tokens", size=28, color=MUTED).move_to([x0 + W / 2, y0 - 0.32, 0])
        r3 = line("2,048 tokens, 40 layers", "160 MiB", -0.1, size=50)
        self.play(FadeIn(r3, shift=0.15 * UP), FadeIn(tok), run_time=0.5)
        self.wait(1.4)

        self.caption("On a 10 gigabit link the bytes alone need 134 ms")
        bw = 10.4
        bar_bg = Rectangle(width=bw, height=0.46, stroke_color=EDGE, stroke_width=2.5, fill_color=PANEL, fill_opacity=1).move_to([-1.3, -1.62, 0])
        tr = ValueTracker(0.0)
        bar = always_redraw(lambda: Rectangle(width=max(0.001, bw * tr.get_value()), height=0.46, stroke_width=0,
                                              fill_color=COLD, fill_opacity=1).align_to(bar_bg, LEFT).align_to(bar_bg, DOWN))
        ms = DecimalNumber(0, num_decimal_places=1, font_size=50, color=NAVY)
        ms.add_updater(lambda m: m.set_value(134.2 * tr.get_value()).next_to(bar_bg, RIGHT, buff=0.25))
        unit = T("ms", size=36, color=NAVY)
        unit.add_updater(lambda m: m.next_to(ms, RIGHT, buff=0.12, aligned_edge=DOWN))
        ms.update(); unit.update()
        f2 = M(r"t_{\mathrm{wire}} = \frac{8\, s_{\mathrm{cache}}}{C} = \frac{8\cdot 160\cdot 2^{20}}{10^{10}}\ \mathrm{s} = 134.2\ \mathrm{ms}", size=38).move_to([0, -2.52, 0])
        self.play(FadeIn(bar_bg), FadeIn(ms), FadeIn(unit), run_time=0.4)
        self.add(bar)
        self.play(tr.animate.set_value(1.0), run_time=2.6, rate_func=linear)
        self.play(Write(f2), run_time=1.2)
        self.hold()
