"""X2: three ways to share one link, as a post office.

One customer has a letter, and every customer ahead brings forty parcels. The three rows are the three rows of
the table on the slide that follows:
  1. one line for everyone: the letter waits for every parcel ahead of it;
  2. a line for letters, and the clerk first finishes the customer at the window: the letter waits for the
     rest of one customer;
  3. a line for letters, and the clerk takes the letter between two parcels: it waits for one parcel.
A letter stands for a small urgent message, the forty parcels of one customer for one large message, and the
window for the link.

The numbers of customers and parcels are made up for the picture; change CUSTOMERS and PARCELS and the bars and
labels follow. The three rows are on the screen from the first frame."""
from style import *
from figures import person, stack, envelope, legend

CUSTOMERS, PARCELS = 3, 40
ROWS = [2.05, 0.15, -1.75]             # centre of each row
XL = -6.98
XW = -1.55                             # the window, in every row
PITCH = 1.15                           # distance between two customers in a line
X0 = 0.45                              # left end of the bars
BW = 2.55                              # width of the longest bar: every parcel ahead
U = BW / (CUSTOMERS * PARCELS)         # width of one parcel in a bar
BH = 0.5
XR = 3.3                               # the text at the right
TITLES = ["One line for everyone",
          "A line for letters: next after this customer",
          "A line for letters: next after this parcel"]


class X2PostOffice(Clip):
    def construct(self):
        gy = [y - 0.62 for y in ROWS]                  # ground of each row
        ys = [y - 0.12 for y in ROWS]                  # centre line of the bars
        slot = lambda k: np.array([XW, gy[k] + 0.68, 0])        # the opening of the window

        def window(k):
            frame = Rectangle(width=0.62, height=1.04, stroke_color=INK, stroke_width=3, fill_color=PANEL, fill_opacity=1).move_to([XW, gy[k] + 0.52, 0])
            hole = Rectangle(width=0.44, height=0.4, stroke_color=INK, stroke_width=2.5, fill_color=BG, fill_opacity=1).move_to(slot(k))
            return VGroup(frame, hole)

        def seg(k, i, n=PARCELS):
            r = Rectangle(width=max(n * U, 0.07), height=BH, stroke_color=COLD, stroke_width=2.5, fill_color=COLDF, fill_opacity=1)
            return r.move_to([X0 + i * PARCELS * U, ys[k], 0], aligned_edge=LEFT)

        def right(k, a, b):
            ta = T(a, size=32, weight=BOLD).move_to([XR, ys[k] + 0.22, 0], aligned_edge=LEFT)
            return VGroup(ta, T(b, size=28, color=MUTED).move_to([XR, ys[k] - 0.24, 0], aligned_edge=LEFT))

        leg = legend([("letter", "a small urgent message"), ("40 parcels", "one large message"), ("window", "the link")], 3.66)
        head = T("Wait of the letter", size=28, color=NAVY, weight=BOLD).move_to([X0, ROWS[0] + 0.72, 0], aligned_edge=LEFT)
        axis = Line([X0, ys[0] + 0.5, 0], [X0, ys[2] - 0.5, 0], color=EDGE, stroke_width=2)
        self.add(leg, head, axis)

        labels, stacks, nums, envs = [], [], [], []
        for k in range(3):
            lab = T(TITLES[k], size=28, color=NAVY if k == 0 else MUTED).move_to([XL, ROWS[k] + 0.72, 0], aligned_edge=LEFT)
            ground = Line([XL, gy[k], 0], [-0.05, gy[k], 0], color=EDGE, stroke_width=3)
            st, nu, people = [], [], []
            for i in range(CUSTOMERS):
                x = XW - 1.22 - i * PITCH
                people.append(person(COLD).shift([x, gy[k], 0]))
                st.append(stack().shift([x + 0.24, gy[k] + 0.02, 0]))
                nu.append(T(str(PARCELS), size=28, color=COLD).move_to([x + 0.44, gy[k] + 0.84, 0]))
            if k == 0:                                 # the letter at the end of the one line
                xl = XW - 1.22 - CUSTOMERS * PITCH
                env = envelope().move_to([xl + 0.38, gy[k] + 0.42, 0])
            else:                                      # the letter first in its own line, on the other side of the window
                xl = XW + 0.95
                env = envelope().move_to([xl - 0.38, gy[k] + 0.42, 0])
            people.append(person(HOT).shift([xl, gy[k], 0]))
            self.add(lab, ground, window(k), *people, *st, *nu, env)
            labels.append(lab); stacks.append(st); nums.append(nu); envs.append(env)

        def serve(k, i, t):
            """The clerk handles every parcel of customer i in row k: its stack fades."""
            return [stacks[k][i].animate.set_opacity(0.18), nums[k][i].animate.set_opacity(0.25)]

        # 1. one line for everyone
        self.caption("One customer has a letter. Everyone ahead has forty parcels", run_time=0)
        self.wait(1.4)
        self.caption("One line: the letter waits for every parcel ahead of it")
        for i in range(CUSTOMERS):
            self.play(GrowFromEdge(seg(0, i), LEFT), *serve(0, i, 0.8), run_time=0.8)
        self.play(envs[0].animate.move_to(slot(0)), run_time=0.7)
        self.play(FadeIn(right(0, "%d parcels" % (CUSTOMERS * PARCELS), "everyone ahead")), run_time=0.4)
        self.wait(1.3)

        # 2. a line for letters; the customer at the window is finished first
        self.caption("A line for letters: the clerk first finishes the customer at the window")
        self.play(labels[0].animate.set_color(MUTED), labels[1].animate.set_color(NAVY), run_time=0.5)
        self.wait(0.5)
        self.play(GrowFromEdge(seg(1, 0), LEFT), *serve(1, 0, 1.0), run_time=1.0)
        self.play(envs[1].animate.move_to(slot(1)), run_time=0.7)
        self.play(FadeIn(right(1, "up to %d parcels" % PARCELS, "rest of one customer")), run_time=0.4)
        self.wait(1.4)

        # 3. the clerk takes the letter between two parcels
        self.caption("If the clerk takes the letter between two parcels, it waits for one")
        self.play(labels[1].animate.set_color(MUTED), labels[2].animate.set_color(NAVY), run_time=0.5)
        self.wait(0.5)
        one = stacks[2][0][-1]                         # the top parcel of the customer at the window
        self.play(one.animate.move_to(slot(2)), run_time=0.7)
        self.play(FadeIn(seg(2, 0, 1)), run_time=0.4)
        self.play(FadeOut(one), envs[2].animate.move_to(slot(2)), run_time=0.7)
        self.play(FadeIn(right(2, "1 parcel", "the one in hand")), run_time=0.4)
        self.wait(1.4)

        # 4. what follows from the design and what is measured
        self.caption("A line for letters is the design. When the clerk switches is what E3 measures", color=NAVY)
        self.play(labels[1].animate.set_color(NAVY), run_time=0.5)
        self.hold()
