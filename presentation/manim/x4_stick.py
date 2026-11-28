"""X4: the rotation of the quantizer as a stick in a room (Lemmas 6.7 and 6.8).

A stick of length 1 lies along one wall of a room. Its shadows on the three edges of the room are the three
coordinates of a vector: one is long and two have no length. One ruler with eight marks has to measure all
three. Turned onto the diagonal of the room, the stick keeps its length, the three shadows are equal, and the
one ruler fits them; turning back gives the same stick again.

The picture has three dimensions and the cache vectors have many more. The length of the ruler is chosen for
the picture (RULER below). The room, the stick, the three bars and the ruler are on the screen from the first
frame."""
from style import *
from figures import legend

O = np.array([-5.7, -2.3, 0])          # the corner of the room where the stick starts
S = 3.7                                # the stick and each edge of the room, on the screen
EX, EY, EZ = np.array([1.0, 0, 0]), np.array([0.46, 0.30, 0]), np.array([0, 1.0, 0])
RULER = 0.75                           # the last mark of the ruler, as a share of the stick
BX0, BU, BH = 1.75, 4.2, 0.5           # left end of the bars, length of a bar of 1.00, height of a bar
YB = [1.05, 0.15, -0.75]               # the three bars
NAMES = ["length", "width", "height"]
A = np.array([1.0, 0.0, 0.0])
B = np.ones(3) / np.sqrt(3)
OMEGA = np.arccos(A @ B)


def P(v):
    return O + S * (v[0] * EX + v[1] * EY + v[2] * EZ)


def turn(s):
    """The unit vector a share s of the way from the wall (s = 0) to the diagonal (s = 1)."""
    return (np.sin((1 - s) * OMEGA) * A + np.sin(s * OMEGA) * B) / np.sin(OMEGA)


class X4Stick(Clip):
    def construct(self):
        t = ValueTracker(0.0)
        vec = lambda: turn(t.get_value())

        leg = legend([("stick", "cache vector"), ("shadow", "coordinate"), ("ruler", "eight levels"), ("turn", "rotation")], 3.66)

        # the room: twelve edges, the three from the corner of the stick drawn darker
        corners = [np.array([i, j, k], dtype=float) for i in (0, 1) for j in (0, 1) for k in (0, 1)]
        edges = VGroup()
        for a in corners:
            for b in corners:
                d = b - a
                if d.sum() == 1 and (d >= 0).all():
                    axis = (a == 0).all()
                    edges.add(Line(P(a), P(b), color=INK if axis else EDGE, stroke_width=4 if axis else 2.5))
        room_labels = VGroup(T("length", size=28, color=MUTED).move_to(P([0.5, 0, 0]) + np.array([0, -0.32, 0])),
                             T("height", size=28, color=MUTED).move_to(P([0, 0, 0.5]) + np.array([-0.2, 0, 0]), aligned_edge=RIGHT),
                             T("width", size=28, color=MUTED).move_to(P([1, 0.5, 0]) + np.array([0.22, -0.02, 0]), aligned_edge=LEFT))

        def guides():
            v = vec()
            f = np.array([v[0], v[1], 0])
            g = VGroup()
            for p, q in [(v, f), (f, [v[0], 0, 0]), (f, [0, v[1], 0]), (v, [0, 0, v[2]])]:
                if np.linalg.norm(P(p) - P(q)) > 0.05:
                    g.add(DashedLine(P(p), P(q), color=MUTED, stroke_width=2.5, dash_length=0.08))
            return g

        def shadows():
            v = vec()
            g = VGroup()
            for k in range(3):
                e = np.zeros(3)
                e[k] = v[k]
                if np.linalg.norm(P(e) - O) > 0.03:
                    g.add(Line(O, P(e), color=NAVY, stroke_width=13, stroke_opacity=0.42))
            return g

        def stick():
            return VGroup(Line(O, P(vec()), color=NAVY, stroke_width=10), Dot(P(vec()), radius=0.11, color=NAVY), Dot(O, radius=0.09, color=NAVY))

        # the bars and the ruler
        zero = Line([BX0, YB[0] + 0.5, 0], [BX0, YB[2] - 0.5, 0], color=EDGE, stroke_width=2)
        xr = BX0 + RULER * BU
        ry = 2.0
        ruler = VGroup(Line([BX0, ry, 0], [xr, ry, 0], color=INK, stroke_width=4),
                       *[Line([BX0 + k * RULER * BU / 8, ry, 0], [BX0 + k * RULER * BU / 8, ry + (0.3 if k == 0 else 0.22), 0], color=INK, stroke_width=4) for k in range(9)])
        marks = VGroup(*[DashedLine([BX0 + k * RULER * BU / 8, ry, 0], [BX0 + k * RULER * BU / 8, YB[2] - 0.42, 0], color=EDGE, stroke_width=1.5, dash_length=0.05) for k in range(1, 9)]).set_z_index(-1)
        rl = T("one ruler with eight marks", size=28, color=MUTED).move_to([BX0, ry + 0.58, 0], aligned_edge=LEFT)
        names = VGroup(*[T(NAMES[k], size=28).move_to([BX0 - 0.22, YB[k], 0], aligned_edge=RIGHT) for k in range(3)])
        sl = VGroup(T("length of the stick", size=28, color=MUTED), T("1.00", size=30, color=NAVY, weight=BOLD)).arrange(RIGHT, buff=0.25).move_to([BX0, -1.75, 0], aligned_edge=LEFT)

        def bar(k):
            def make():
                val = abs(vec()[k])
                g = VGroup()
                inside = min(val, RULER)
                if inside > 0.004:
                    g.add(Rectangle(width=inside * BU, height=BH, stroke_width=0, fill_color=NAVY, fill_opacity=1).move_to([BX0, YB[k], 0], aligned_edge=LEFT))
                if val > RULER + 0.004:                # the part past the last mark
                    ex = Rectangle(width=(val - RULER) * BU, height=BH, stroke_width=0, fill_color=LIGHT, fill_opacity=1).move_to([xr, YB[k], 0], aligned_edge=LEFT)
                    g.add(ex, DashedVMobject(Rectangle(width=(val - RULER) * BU, height=BH, color=NAVY, stroke_width=3).move_to(ex), num_dashes=max(6, int(30 * (val - RULER) / 0.25))))
                g.add(T("%.2f" % val, size=30).move_to([BX0 + val * BU + 0.18, YB[k], 0], aligned_edge=LEFT))
                return g
            return always_redraw(make)

        self.add(leg, edges, room_labels, always_redraw(shadows), always_redraw(guides), always_redraw(stick),
                 zero, marks, ruler, rl, names, sl, *[bar(k) for k in range(3)])

        # 1. the stick along a wall
        self.caption("A stick lies along one wall of a room", run_time=0)
        self.wait(1.2)
        self.caption("Its shadows on the three edges: one is long, two have no length")
        self.wait(1.7)

        # 2. one ruler for all three
        self.caption("One ruler with eight marks has to measure all three shadows")
        self.play(rl.animate.set_color(NAVY), run_time=0.5)
        self.wait(1.2)
        self.caption("The long shadow runs past the last mark, and two use no mark at all")
        self.wait(1.8)

        # 3. the turn
        self.caption("Turn the stick onto the diagonal of the room. Its length stays 1.00")
        self.play(t.animate.set_value(1.0), run_time=3.2, rate_func=smooth)
        self.wait(0.6)
        self.caption("Now the three shadows are equal, and the one ruler fits them all")
        self.wait(1.8)

        # 4. the turn can be undone
        self.caption("Turning back gives the same stick again, so the turn loses nothing")
        self.play(t.animate.set_value(0.0), run_time=2.0, rate_func=smooth)
        self.wait(0.4)
        self.play(t.animate.set_value(1.0), run_time=2.0, rate_func=smooth)
        self.wait(0.4)

        # 5. the two lemmas in the words of the picture
        self.caption("Lemmas 6.7 and 6.8: same length, even spread on average, and it can be undone", color=NAVY)
        self.hold()
