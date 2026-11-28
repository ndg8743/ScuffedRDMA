"""X3: the blob channel as a wall of eight parcel lockers (Propositions 5.1 to 5.4).

A locker stands for a receive slot, a token for a credit and a box for a chunk of a layer. The courier holds one
token for each locker and hands it in with a box; the token comes back after the customer has emptied the
locker. Four short scenes on the same picture, one for each proposition:
  5.1  a locker in use gets no second box, because its token is away until the locker is emptied;
  5.2  the door sends the arrival message as it closes, so the message does not come before the box;
  5.3  every box names its order and its place in it, so the order of arrival does not matter;
  5.4  with eight lockers at most eight boxes are under way, so the pace is set by how fast tokens return.

The courier, the tokens, the lockers and the customer are on the screen from the first frame."""
from style import *
from figures import person, legend

N, COLS = 8, 4
LW, LH = 1.25, 1.15                    # one locker
LX0, GY = -2.1, -0.75                  # left edge of the wall, and the ground
PITCH = 0.52                           # distance between two tokens in the tray
TX, TY = -4.1, GY + 1.15               # centre of the tray of tokens
LANE = GY - 0.75                       # the route on which tokens return
HAND = np.array([-5.72, GY + 1.0, 0])  # where the courier holds a box
TAKE = np.array([5.0, GY + 1.0, 0])    # where the customer takes one


def cell(k):
    c, r = k % COLS, k // COLS
    return np.array([LX0 + (c + 0.5) * LW, GY + (1.5 - r) * LH, 0])


def home(k):                           # the place of token k in the tray
    c, r = k % COLS, k // COLS
    return np.array([TX + (c - 1.5) * PITCH, TY + (0.5 - r) * PITCH, 0])


def badge(k):                          # where a token sits on its locker while the locker is in use
    return cell(k) + np.array([0.39, 0.34, 0])


def slot(k):                           # where a box sits in its locker
    return cell(k) + np.array([-0.15, -0.15, 0])


def box(text=None):
    g = VGroup(Rectangle(width=0.75, height=0.65, stroke_color=COLD, stroke_width=2.5, fill_color=COLDF, fill_opacity=1))
    if text:
        g.add(T(text, size=32, color=COLD, weight=BOLD).move_to(g[0]))
    return g


class X3Lockers(Clip):
    def construct(self):
        leg = legend([("locker", "receive slot"), ("token", "credit"), ("box", "chunk of a layer")], 3.66)
        ground = Line([-6.98, GY, 0], [6.98, GY, 0], color=EDGE, stroke_width=3)
        wall = VGroup(*[Rectangle(width=LW, height=LH, stroke_color=INK, stroke_width=3, fill_color=BG, fill_opacity=1).move_to(cell(k)) for k in range(N)])
        courier = person(NAVY, 1.9).shift([-6.25, GY, 0])
        customer = person(NAVY, 1.9).shift([5.75, GY, 0])
        cl = VGroup(T("courier", size=28, color=MUTED), T("(sender)", size=28, color=MUTED)).arrange(DOWN, buff=0.1).move_to([-6.25, GY - 0.62, 0])
        ul = VGroup(T("customer", size=28, color=MUTED), T("(receiver)", size=28, color=MUTED)).arrange(DOWN, buff=0.1).move_to([5.75, GY - 0.62, 0])
        tray = RoundedRectangle(width=4 * PITCH + 0.3, height=2 * PITCH + 0.3, corner_radius=0.1, stroke_color=EDGE, stroke_width=2.5, fill_color=PANEL, fill_opacity=1).move_to([TX, TY, 0])
        tl = T("tokens", size=28, color=HOT).move_to([TX, TY + PITCH + 0.42, 0])
        chips = [Dot(home(k), radius=0.19, color=HOTF).set_stroke(HOT, 2).set_z_index(3) for k in range(N)]
        lane = DashedVMobject(VMobject(color=HOT, stroke_width=3).set_points_as_corners([[LX0 + COLS * LW, LANE, 0], [TX, LANE, 0], [TX, TY - PITCH - 0.2, 0]]), num_dashes=52)
        tip = Triangle(color=HOT, fill_color=HOT, fill_opacity=1, stroke_width=0).scale(0.12).move_to([TX, TY - PITCH - 0.22, 0])
        ll = T("tokens return on the fast route", size=28, color=HOT).move_to([(TX + LX0 + COLS * LW) / 2, LANE - 0.42, 0])
        tag = T("Proposition 5.1", size=30, color=NAVY, weight=BOLD).move_to([6.98, 3.02, 0], aligned_edge=RIGHT)
        self.add(leg, ground, wall, courier, customer, cl, ul, tray, tl, lane, tip, ll, *chips, tag)

        def put(k, b, rt=0.9):
            b.move_to(HAND)
            self.play(chips[k].animate.move_to(badge(k)), FadeIn(b), run_time=0.5)
            self.play(b.animate.move_to(slot(k)), run_time=rt)

        def back_path(k):
            return VMobject().set_points_as_corners([badge(k), [badge(k)[0], LANE, 0], [home(k)[0], LANE, 0], home(k)])

        def new_tag(s):
            nonlocal tag
            t = T(s, size=30, color=NAVY, weight=BOLD).move_to([6.98, 3.02, 0], aligned_edge=RIGHT)
            self.play(FadeOut(tag), FadeIn(t), run_time=0.4)
            tag = t

        # ---- 5.1: a locker in use gets no second box
        self.caption("The courier has one token for each locker", run_time=0)
        self.wait(1.3)
        self.caption("A box goes in together with the token of that locker")
        b = box()
        put(1, b)
        self.wait(0.4)
        self.caption("While the locker is full its token is away, so no second box goes in")
        ring = DashedVMobject(Circle(radius=0.23, color=HOT, stroke_width=3).move_to(home(1)), num_dashes=10)
        frame = Rectangle(width=LW, height=LH, stroke_color=NAVY, stroke_width=7).move_to(cell(1)).set_z_index(2)
        self.play(Create(ring), Create(frame), run_time=0.7)
        self.wait(1.0)
        self.caption("The token returns after the customer has emptied the locker")
        self.play(FadeOut(frame), b.animate.move_to(TAKE), run_time=1.0)
        self.play(FadeOut(b), run_time=0.3)
        self.play(MoveAlongPath(chips[1], back_path(1)), FadeOut(ring), run_time=1.3)
        self.wait(0.5)

        # ---- 5.2: the message does not come before the box
        new_tag("Proposition 5.2")
        self.caption("The door sends the arrival message as it closes on the box")
        b = box()
        put(6, b)
        door = Rectangle(width=LW - 0.1, height=LH - 0.1, stroke_color=INK, stroke_width=2.5, fill_color=PANEL, fill_opacity=0.9).move_to(cell(6)).set_z_index(2)
        msg = VGroup(RoundedRectangle(width=0.56, height=0.36, corner_radius=0.08, stroke_color=COLD, stroke_width=3, fill_color=BG, fill_opacity=1),
                     Line([-0.15, 0, 0], [0.15, 0, 0], color=COLD, stroke_width=3)).move_to(cell(6) + np.array([0.7, 0, 0])).set_z_index(4)
        self.play(GrowFromEdge(door, LEFT), FadeIn(msg), run_time=0.7)
        self.play(msg.animate.move_to([5.75, GY + 2.2, 0]), run_time=1.0)
        arrived = T("box is in", size=28, color=COLD).next_to(msg, LEFT, buff=0.14)
        self.play(FadeIn(arrived), run_time=0.3)
        self.wait(0.9)
        self.play(FadeOut(door), FadeOut(msg), FadeOut(arrived), b.animate.move_to(TAKE), run_time=0.9)
        self.play(FadeOut(b), MoveAlongPath(chips[6], back_path(6)), run_time=1.1)

        # ---- 5.3: the order of arrival does not matter
        new_tag("Proposition 5.3")
        self.caption("Every box names its order and its place in it")
        order = ["3", "1", "2"]
        bs = [box(t) for t in order]
        for k, bx in enumerate(bs):
            put(k, bx, rt=0.6)
        card = VGroup(RoundedRectangle(width=4.5, height=0.58, corner_radius=0.1, stroke_color=EDGE, stroke_width=2.5, fill_color=PANEL, fill_opacity=1),
                      T("label: order 17, box 3 of 3", size=28)).move_to([0.4, 2.3, 0])
        tie = Line(card.get_left() + np.array([0.35, -0.29, 0]), bs[0].get_top() + np.array([0, 0.04, 0]), color=EDGE, stroke_width=2.5)
        self.play(FadeIn(card), Create(tie), run_time=0.5)
        self.wait(1.1)
        self.caption("So the customer puts them in order, whatever order they came in")
        shelf = Line([4.0, -2.62, 0], [6.9, -2.62, 0], color=EDGE, stroke_width=3)
        place = {"1": 4.55, "2": 5.4, "3": 6.25}
        self.play(FadeOut(card), FadeOut(tie), Create(shelf), run_time=0.4)
        self.play(*[bx.animate.move_to([place[t], -2.62 + 0.35, 0]) for t, bx in zip(order, bs)], run_time=1.4)
        self.play(*[MoveAlongPath(chips[k], back_path(k)) for k in range(3)], run_time=1.1)
        self.wait(0.5)

        # ---- 5.4: at most eight boxes are under way
        new_tag("Proposition 5.4")
        self.caption("With eight lockers, at most eight boxes are under way at once")
        full = [box().move_to(HAND) for _ in range(N)]
        self.play(*[chips[k].animate.move_to(badge(k)) for k in range(N)], *[FadeIn(f) for f in full], run_time=0.5)
        self.play(LaggedStart(*[full[k].animate.move_to(slot(k)) for k in range(N)], lag_ratio=0.12), run_time=2.0)
        wait = T("no token left: the courier waits", size=30, weight=BOLD).move_to([-3.9, 2.3, 0])
        self.play(FadeIn(wait), run_time=0.4)
        self.wait(1.0)
        self.play(FadeOut(wait), LaggedStart(*[f.animate.move_to(TAKE).set_opacity(0) for f in full], lag_ratio=0.08), run_time=1.3)
        self.play(LaggedStart(*[MoveAlongPath(chips[k], back_path(k)) for k in range(N)], lag_ratio=0.1), run_time=1.9)
        self.caption("So throughput is at most 8 lockers × locker size ÷ time for a token to return", color=NAVY)
        self.hold()
