"""H1: Amdahl's law in a simple example, the time to dig a hole 1 meter deep.

Three rows: one worker with one shovel, ten workers with one shovel, ten workers with ten shovels.
The share of the digging that can be divided among the workers (P) is an assumed value; change T1, P and N below
and every number and bar on the screen follows.

The three cases are on the screen from the first frame, and the animation adds the bars and the times. A viewer
that shows a GIF as a still picture (PowerPoint outside the slide show, a preview on a phone) therefore shows
the three cases and not an almost empty frame."""
from style import *

T1, P, N = 60.0, 0.8, 10               # minutes for one worker, share that can be divided (assumed), workers
SEQ_MIN = (1 - P) * T1                 # 12 minutes that cannot be shared
PAR_MIN = P * T1                       # 48 minutes that can
TN = SEQ_MIN + PAR_MIN / N             # 16.8 minutes with N workers
SEQ = "#c9ced6"                        # fill of the part that cannot be shared (light gray, dark edge)
X0, U, BH = -1.85, 0.1, 0.56           # left end of the bars, width of one minute, height of a bar
ROWS = [2.30, 0.35, -1.60]             # centre of each row
XL = -6.98                             # left edge of the pictures


def num(v):
    return ("%.1f" % v).rstrip("0").rstrip(".")


def worker(color, shovel=False, flip=False):
    """A standing figure 0.93 high with its feet at the origin. With a shovel it reaches 0.33 to the right."""
    sw = 5
    g = VGroup(
        Circle(radius=0.13, stroke_width=0, fill_color=color, fill_opacity=1).move_to([0, 0.80, 0]),
        Line([0, 0.67, 0], [0, 0.30, 0], color=color, stroke_width=sw),
        Line([0, 0.30, 0], [-0.13, 0, 0], color=color, stroke_width=sw),
        Line([0, 0.30, 0], [0.13, 0, 0], color=color, stroke_width=sw))
    if shovel:
        g.add(Line([0, 0.58, 0], [0.17, 0.43, 0], color=color, stroke_width=sw),
              Line([0.09, 0.66, 0], [0.26, 0.05, 0], color=color, stroke_width=4),
              Polygon([0.19, 0.10, 0], [0.33, 0.06, 0], [0.30, -0.07, 0], [0.21, -0.04, 0],
                      stroke_width=0, fill_color=color, fill_opacity=1))
    else:
        g.add(Line([0, 0.58, 0], [-0.13, 0.34, 0], color=color, stroke_width=sw),
              Line([0, 0.58, 0], [0.13, 0.34, 0], color=color, stroke_width=sw))
    if flip:
        g.flip(UP, about_point=ORIGIN)
    return g


def ground(y, x_hole, x_b=-2.25, hw=0.5, depth=0.26):
    """Ground line with one hole in it."""
    a, b = x_hole - hw / 2, x_hole + hw / 2
    pit = VMobject(color=EDGE, stroke_width=3).set_points_as_corners([[a, y, 0], [a, y - depth, 0], [b, y - depth, 0], [b, y, 0]])
    return VGroup(Line([XL, y, 0], [a, y, 0], color=EDGE, stroke_width=3), pit, Line([b, y, 0], [x_b, y, 0], color=EDGE, stroke_width=3))


class H1AmdahlDig(Clip):
    def construct(self):
        ys = [y - 0.15 for y in ROWS]                  # centre line of the bars
        gy = [y - 0.62 for y in ROWS]                  # ground of each row

        def label(k, s):
            return T(s, size=28, color=NAVY if k == 0 else MUTED).move_to([XL, ROWS[k] + 0.70, 0], aligned_edge=LEFT)

        def bar(k, minutes, x=X0):
            return Rectangle(width=minutes * U, height=BH, stroke_width=0, fill_color=NAVY, fill_opacity=1).move_to([x, ys[k], 0], aligned_edge=LEFT)

        def seq(k):
            r = Rectangle(width=SEQ_MIN * U, height=BH, stroke_color=EDGE, stroke_width=2.5, fill_color=SEQ, fill_opacity=1)
            return r.move_to([X0, ys[k], 0], aligned_edge=LEFT)

        def right(k, a, b=None):
            ta = T(a, size=34, weight=BOLD)
            if b is None:
                return VGroup(ta.move_to([4.45, ys[k], 0], aligned_edge=LEFT))
            ta.move_to([4.45, ys[k] + 0.22, 0], aligned_edge=LEFT)
            return VGroup(ta, T(b, size=28, color=MUTED).move_to([4.45, ys[k] - 0.24, 0], aligned_edge=LEFT))

        head = T("Time to dig a hole 1 meter deep", size=30, color=NAVY, weight=BOLD).move_to([X0, 3.62, 0], aligned_edge=LEFT)
        axis = Line([X0, ys[0] + 0.5, 0], [X0, ys[2] - 0.5, 0], color=EDGE, stroke_width=2)
        self.add(head, axis)

        # the three cases, on the screen from the first frame; the label of the case in turn is navy
        l1 = label(0, "1 worker, 1 shovel")
        g1 = ground(gy[0], -6.05)
        w1 = worker(NAVY, shovel=True).shift([-6.50, gy[0], 0])
        l2 = label(1, "%d workers, 1 shovel (nine idle)" % N)
        g2 = ground(gy[1], -6.05)
        w2 = worker(NAVY, shovel=True).shift([-6.50, gy[1], 0])
        idle = VGroup(*[worker(EDGE).shift([-5.35 + 0.36 * k, gy[1], 0]) for k in range(N - 1)])
        l3 = label(2, "%d workers, %d shovels" % (N, N))
        xh = -4.62
        g3 = ground(gy[2], xh)
        half = N // 2
        crowd = VGroup(*[worker(NAVY, shovel=True).shift([xh - 0.45 - 0.42 * k, gy[2], 0]) for k in range(half)],
                       *[worker(NAVY, shovel=True, flip=True).shift([xh + 0.45 + 0.42 * k, gy[2], 0]) for k in range(N - half)])
        self.add(l1, g1, w1, l2, g2, w2, idle, l3, g3, crowd)

        # 1. one worker, one shovel
        self.caption("One worker with one shovel digs 1 meter in an hour", run_time=0)
        self.wait(0.8)
        b1 = bar(0, T1)
        r1 = right(0, num(T1) + " min")
        self.play(GrowFromEdge(b1, LEFT), run_time=2.0)
        self.play(FadeIn(r1), run_time=0.4)
        self.wait(1.3)

        # 2. ten workers, still one shovel
        self.caption("Nine more workers, still one shovel: nine are idle and it takes an hour")
        self.play(l1.animate.set_color(MUTED), l2.animate.set_color(NAVY), run_time=0.5)
        self.wait(0.6)
        b2 = bar(1, T1)
        r2 = right(1, num(T1) + " min", "speed-up 1")
        self.play(GrowFromEdge(b2, LEFT), run_time=2.0)
        self.play(FadeIn(r2), run_time=0.4)
        self.wait(1.4)

        # 3. ten workers, ten shovels, one hole
        self.caption("Ten shovels: ten workers get in each other's way in one hole")
        self.play(l2.animate.set_color(MUTED), l3.animate.set_color(NAVY), run_time=0.5)
        self.wait(0.6)
        xm = X0 + T1 / N * U
        mark = DashedLine([xm, ys[2] + 0.42, 0], [xm, ys[2] - 0.42, 0], color=INK, stroke_width=3, dash_length=0.09).set_z_index(3)
        mt = T("%d times faster would be %s min" % (N, num(T1 / N)), size=28, color=MUTED).move_to([xm + 0.14, ys[2] + 0.56, 0], aligned_edge=LEFT)
        self.play(Create(mark), FadeIn(mt), run_time=0.6)
        self.wait(1.6)

        # 4. the assumption: part of the digging cannot be shared
        self.caption("Assume that %s of the %s minutes cannot be shared among the workers" % (num(SEQ_MIN), num(T1)))
        s1, s2 = seq(0), seq(1)
        n1 = VGroup(T(num(SEQ_MIN), size=28).move_to(s1), T(num(PAR_MIN), size=28, color=WHITE).move_to([X0 + (SEQ_MIN + PAR_MIN / 2) * U, ys[0], 0]))
        n2 = VGroup(T(num(SEQ_MIN), size=28).move_to(s2), T(num(PAR_MIN), size=28, color=WHITE).move_to([X0 + (SEQ_MIN + PAR_MIN / 2) * U, ys[1], 0]))
        chip_a = Square(0.28, stroke_color=EDGE, stroke_width=2.5, fill_color=SEQ, fill_opacity=1)
        chip_b = Square(0.28, stroke_width=0, fill_color=NAVY, fill_opacity=1)
        leg = VGroup(T("Assumed:", size=28, color=MUTED),
                     VGroup(chip_a, T("cannot be shared", size=28)).arrange(RIGHT, buff=0.14),
                     VGroup(chip_b, T("can be shared", size=28)).arrange(RIGHT, buff=0.14)).arrange(RIGHT, buff=0.38)
        leg.move_to([X0, ROWS[0] + 0.70, 0], aligned_edge=LEFT)
        self.play(FadeIn(s1), FadeIn(s2), FadeIn(n1), FadeIn(n2), FadeIn(leg), run_time=1.0)
        self.wait(1.8)

        # 5. the time by Amdahl's law
        self.caption("Amdahl's law gives the time: %s minutes, which is %s times faster" % (num(TN), num(T1 / TN)))
        s3 = seq(2)                                    # no number in this one: the dashed line at 6 minutes crosses its middle
        self.play(TransformFromCopy(s1, s3), run_time=1.1)
        self.wait(0.3)
        src = bar(0, PAR_MIN, x=X0 + SEQ_MIN * U)
        p3 = bar(2, PAR_MIN / N, x=X0 + SEQ_MIN * U)
        self.play(TransformFromCopy(src, p3), run_time=1.6)
        r3 = right(2, num(TN) + " min", "speed-up " + num(T1 / TN))
        f = M(r"%s\ \text{min} + \frac{%s\ \text{min}}{%d} = %s\ \text{min}" % (num(SEQ_MIN), num(PAR_MIN), N, num(TN)), size=40).move_to([2.35, -2.64, 0])
        self.play(FadeIn(r3), FadeIn(f), run_time=0.7)
        self.hold()
