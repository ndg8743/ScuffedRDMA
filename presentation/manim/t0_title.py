"""T0: title strip. Small urgent messages pass while bulk blocks move slowly. Loops without a seam."""
from style import *

config.frame_height = 14.222 * 200 / 1600
config.frame_width = 14.222


class T0Title(Scene):
    def construct(self):
        period = 12.0
        yh, yc = 0.5, -0.36
        hot_lane = VGroup(Line([-7.2, yh - 0.26, 0], [7.2, yh - 0.26, 0], color=HOT, stroke_width=3),
                          Line([-7.2, yh + 0.26, 0], [7.2, yh + 0.26, 0], color=HOT, stroke_width=3))
        cold_lane = VGroup(Line([-7.2, yc - 0.4, 0], [7.2, yc - 0.4, 0], color=COLD, stroke_width=3),
                           Line([-7.2, yc + 0.4, 0], [7.2, yc + 0.4, 0], color=COLD, stroke_width=3))
        span = 16.0
        t = ValueTracker(0.0)
        hots, colds = VGroup(), VGroup()
        for k in range(4):                       # 4 hot messages, each crosses 2 spans per period
            d = Square(0.3, stroke_color=HOT, stroke_width=2.5, fill_color=HOTF, fill_opacity=1)
            d.add_updater(lambda m, k=k: m.move_to([-8 + ((k * span / 4 + 2 * span * t.get_value() / period) % span), yh, 0]))
            hots.add(d)
        for k in range(5):                       # 5 bulk blocks, one span per period
            r = RoundedRectangle(width=2.6, height=0.58, corner_radius=0.08, stroke_color=COLD, stroke_width=2.5, fill_color=COLDF, fill_opacity=1)
            r.add_updater(lambda m, k=k: m.move_to([-8 + ((k * span / 5 + span * t.get_value() / period) % span), yc, 0]))
            colds.add(r)
        self.add(hot_lane, cold_lane, hots, colds)
        self.play(t.animate.set_value(period), run_time=period, rate_func=linear)
