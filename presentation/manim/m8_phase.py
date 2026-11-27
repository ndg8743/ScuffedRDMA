"""M8: what the static phase detector answers during decoding (Proposition 6.1)."""
from style import *

L = 40


class M8PhaseDetector(Clip):
    def construct(self):
        cw = 0.92
        y = 1.15
        start = 24                      # the window first shows layers 24..31
        n0 = start - 2
        tape = VGroup()
        for n in range(n0, start + 8 + 40 + 9):
            lay = n % L
            sq = Square(cw, stroke_color=EDGE, stroke_width=2.5, fill_color=BG, fill_opacity=1)
            sq.move_to([(n - start - 3.5) * cw, y, 0])
            tx = Integer(lay, font_size=40, color=INK).move_to(sq)
            tape.add(VGroup(sq, tx))
        win = Rectangle(width=8 * cw + 0.1, height=cw + 0.18, stroke_color=NAVY, stroke_width=8).move_to([0, y, 0])
        wl = T("the last 8 layer numbers", size=30, color=NAVY).next_to(win, UP, buff=0.18)
        last3 = Line([1.5 * cw + 0.06, y - cw / 2 - 0.2, 0], [4 * cw, y - cw / 2 - 0.2, 0], color=HOT, stroke_width=8)
        l3 = T("last three", size=28, color=HOT).next_to(last3, DOWN, buff=0.1)
        cover_l = Rectangle(width=3.4, height=cw + 0.5, stroke_width=0, fill_color=BG, fill_opacity=0.72).move_to([-4 * cw - 0.05 - 1.7, y, 0])
        cover_r = Rectangle(width=3.4, height=cw + 0.5, stroke_width=0, fill_color=BG, fill_opacity=0.72).move_to([4 * cw + 0.05 + 1.7, y, 0])
        note = T("decoding: each new token updates layers 0, 1, ..., 39 in order", size=30, color=MUTED).move_to([0, 3.55, 0])

        def verdict_of(last):
            # window ends at layer `last`; a wrap inside the window means the run is broken
            return "unknown" if last <= 6 else "prefill"

        rules = VGroup(
            VGroup(T("prefill", size=32, color=COLD, weight=BOLD), T("each number is one more than the one before", size=30)).arrange(RIGHT, buff=0.3),
            VGroup(T("decode", size=32, color=HOT, weight=BOLD), T("the last three numbers are equal", size=30)).arrange(RIGHT, buff=0.3),
            VGroup(T("unknown", size=32, color=MUTED, weight=BOLD), T("anything else", size=30)).arrange(RIGHT, buff=0.3),
        ).arrange(DOWN, buff=0.22, aligned_edge=LEFT).move_to([-2.15, -1.55, 0])
        cnt = {"prefill": 0, "unknown": 0, "decode": 0}
        nums = {k: Integer(0, font_size=50, color=c) for k, c in (("prefill", COLD), ("decode", HOT), ("unknown", MUTED))}
        for k, r in zip(("prefill", "decode", "unknown"), rules):
            nums[k].move_to([4.3, r.get_center()[1], 0])
        ch = T("answers", size=28, color=MUTED).move_to([4.3, rules.get_top()[1] + 0.45, 0])
        self.add(tape, cover_l, cover_r, win, wl, note, rules, *nums.values(), ch)
        self.caption("What the static detector sees while the model is decoding", run_time=0)
        self.wait(2.4)
        self.caption("A rising run looks like prefill. At the wrap from 39 to 0 it says unknown")
        cur = None
        for step in range(40):
            last = (start + 7 + step + 1) % L
            v = verdict_of(last)
            cnt[v] += 1
            hi = SurroundingRectangle(rules[{"prefill": 0, "decode": 1, "unknown": 2}[v]][0], color=INK, buff=0.08, stroke_width=4, corner_radius=0.06)
            anims = [tape.animate.shift(LEFT * cw)]
            self.play(*anims, run_time=0.2 if 0 < step < 39 else 0.4, rate_func=linear)
            nums[v].set_value(cnt[v])
            if cur is not None:
                self.remove(cur)
            self.add(hi); cur = hi
            if step in (8, 9):
                self.wait(0.35)
        self.wait(0.6)
        self.remove(cur)
        self.caption("Consecutive layer numbers differ, so it does not answer decode")
        self.play(FadeIn(last3), FadeIn(l3), run_time=0.5)
        pct = VGroup(T("82.5 %", size=34, color=COLD, weight=BOLD).next_to(nums["prefill"], RIGHT, buff=0.35),
                     T("0 %", size=34, color=HOT, weight=BOLD).next_to(nums["decode"], RIGHT, buff=0.35),
                     T("17.5 %", size=34, color=MUTED, weight=BOLD).next_to(nums["unknown"], RIGHT, buff=0.35))
        self.play(FadeIn(pct, shift=0.15 * RIGHT), Circumscribe(nums["decode"], color=HOT, stroke_width=5), run_time=1.0)
        self.hold()
