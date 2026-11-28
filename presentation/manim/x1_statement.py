"""X1: Proposition 2.1 as a bank statement.

Each line of a statement shows an amount and the balance after it. A balance is computed from the lines above
it, so a new line changes no earlier balance, and another branch can carry on from a copy of the statement.
In the model a line is a token, a balance is the keys and values of that token, the statement is the cache and
the other branch is the decode server.

The amounts are made up for the picture. Both sheets, the first four lines and the legend are on the screen
from the first frame."""
from style import *
from figures import check, entry

LINES = [(1, 120), (2, -45), (3, 30), (4, -20), (5, 50), (6, -15)]      # line number, amount
XL = -6.98
AX0, AX1 = -6.98, -0.85                # sheet of branch A, left and right edge
DX = 7.83                              # sheet of branch B = sheet A shifted by DX
YT, YB = 3.28, -1.12                   # top and bottom of the sheets
YH = 2.86                              # column heads
YR = [2.17 - 0.55 * k for k in range(6)]
XLINE, XAMT, XBAL, XCHK = -6.68, -3.95, -2.05, -1.38


def amount(v):
    return ("+ %d" % v) if v > 0 else ("− %d" % -v)



class X1Statement(Clip):
    def construct(self):
        bal, s = [], 0
        for _, a in LINES:
            s += a
            bal.append(s)

        def sheet(dx, title, color):
            frame = Rectangle(width=AX1 - AX0, height=YT - YB, stroke_color=EDGE, stroke_width=2.5, fill_color=BG, fill_opacity=1)
            frame.move_to([(AX0 + AX1) / 2 + dx, (YT + YB) / 2, 0])
            t = T(title, size=30, color=color, weight=BOLD).move_to([AX0 + dx, YT + 0.36, 0], aligned_edge=LEFT)
            heads = VGroup(T("Line", size=28, color=MUTED).move_to([XLINE + dx, YH, 0], aligned_edge=LEFT),
                           T("Amount", size=28, color=MUTED).move_to([XAMT + dx, YH, 0], aligned_edge=RIGHT),
                           T("Balance", size=28, color=MUTED).move_to([XBAL + dx, YH, 0], aligned_edge=RIGHT))
            rule = Line([AX0 + 0.25 + dx, YH - 0.27, 0], [AX1 - 0.25 + dx, YH - 0.27, 0], color=EDGE, stroke_width=2)
            return frame, t, heads, rule

        def row(k, dx=0.0):
            n, a = LINES[k]
            return VGroup(T(str(n), size=30).move_to([XLINE + 0.12 + dx, YR[k], 0], aligned_edge=LEFT),
                          T(amount(a), size=30).move_to([XAMT + dx, YR[k], 0], aligned_edge=RIGHT),
                          T(str(bal[k]), size=30, weight=BOLD).move_to([XBAL + dx, YR[k], 0], aligned_edge=RIGHT))

        fa, ta, ha, ra = sheet(0, "Statement at branch A", NAVY)
        fb, tb, hb, rb = sheet(DX, "Copy at branch B", MUTED)
        rows = [row(k) for k in range(4)]

        legend = VGroup(entry("line", "a token", XL, -1.78), entry("balance", "its keys and values", XL, -2.36),
                        entry("statement", "the cache", 0.85, -1.78), entry("branch B", "the decode server", 0.85, -2.36))
        self.add(fa, ta, ha, ra, fb, tb, hb, rb, *rows, legend)

        # 1. what a line is
        self.caption("Each line shows an amount and the balance after it", run_time=0)
        self.wait(1.6)

        # 2. a balance is computed from the lines above it
        self.caption("A balance is computed from the lines above it")
        hl = Rectangle(width=1.75, height=3 * 0.55, stroke_width=0, fill_color=AMBER, fill_opacity=0.35)
        hl.move_to([XAMT - 0.72, (YR[0] + YR[2]) / 2, 0]).set_z_index(-1)
        fa.set_z_index(-2)
        box = Rectangle(width=1.05, height=0.5, stroke_color=NAVY, stroke_width=4).move_to([XBAL - 0.36, YR[2], 0])
        calc = T("120 − 45 + 30 = 105", size=30, color=NAVY).move_to([(AX0 + AX1) / 2, YR[5], 0])
        self.play(FadeIn(hl), run_time=0.5)
        self.play(Create(box), FadeIn(calc), run_time=0.7)
        self.wait(1.7)
        self.play(FadeOut(hl), FadeOut(box), FadeOut(calc), run_time=0.5)

        # 3. a new line changes no earlier balance
        self.caption("A new line is added. No balance above it changes")
        r5 = row(4)
        self.play(FadeIn(r5[0], shift=0.2 * UP), FadeIn(r5[1], shift=0.2 * UP), run_time=0.7)
        self.wait(0.3)
        self.play(FadeIn(r5[2]), run_time=0.5)
        checks = [check().move_to([XCHK, YR[k], 0]) for k in range(4)]
        self.play(LaggedStart(*[Create(c) for c in checks], lag_ratio=0.35), run_time=1.6)
        same = T("lines 1 to 4: unchanged", size=28, color=NAVY).move_to([(AX0 + AX1) / 2, YR[5], 0])
        self.play(FadeIn(same), run_time=0.4)
        self.wait(1.6)

        # 4. the statement is kept, not added up again
        self.caption("So the statement is kept, and the old lines are not added up again")
        self.wait(1.8)

        # 5. another branch carries on from a copy
        self.caption("Another branch carries on from a copy of the same statement")
        arrow = Arrow([AX1 + 0.08, YR[2], 0], [AX0 + DX - 0.08, YR[2], 0], color=NAVY, stroke_width=6, buff=0, max_tip_length_to_length_ratio=0.22)
        al = T("copy", size=28, color=NAVY).next_to(arrow, UP, buff=0.12)
        self.play(GrowArrow(arrow), FadeIn(al), tb.animate.set_color(NAVY), run_time=0.8)
        src = VGroup(*rows, r5)
        dst = VGroup(*[row(k, DX) for k in range(5)])
        self.play(TransformFromCopy(src, dst), run_time=1.8)
        self.wait(0.6)
        r6 = row(5, DX)
        self.play(FadeIn(r6[0], shift=0.2 * UP), FadeIn(r6[1], shift=0.2 * UP), run_time=0.7)
        self.play(FadeIn(r6[2]), run_time=0.5)
        self.wait(1.4)

        # 6. the statement of the proposition in the words of the model
        self.caption("Proposition 2.1: a new token changes no earlier row of the cache", color=NAVY)
        self.hold()
