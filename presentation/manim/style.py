"""Shared look for the defense-deck animations: white background, the thesis figure palette, large type.

Sizes: at the width the animations have on a slide, Text 32 is about 19 pt and MathTex 40 about 19 pt.
Nothing that must be read is smaller than Text 28 or MathTex 36."""
from manim import *
import numpy as np

BG = "#ffffff"
PANEL = "#f1f3f6"      # light fill of boxes
EDGE = "#7d8590"       # box borders, axes
INK = "#1a202c"        # dInk
MUTED = "#5c6066"      # dGray
NAVY = "#173a79"       # university blue: emphasis, frames
COLD = "#005ab5"       # dBlue: bulk traffic, the cache
COLDF = "#cfe2f5"      # tint of dBlue
HOT = "#b04800"        # dOrange: text and lines of the urgent class
HOTF = "#f4741c"       # bright orange fill
SPILL = "#005ab5"      # (was purple) sign sketch and storage now use the blue of the palette
OKC = "#173a79"        # (was green) proved, guaranteed: navy
BAD = "#b04800"        # (was red) issue: the dark orange of the palette
AMBER = "#8fbbe9"      # (was amber) highlight fill: light blue
COLDL = "#4a9ee8"      # lighter blue for a second frame
LIGHT = "#e3e7ec"      # light gray fill
FONT = "Carlito"; MONO = "DejaVu Sans Mono"
config.background_color = BG
Text.set_default(color=INK)
MathTex.set_default(color=INK)
Tex.set_default(color=INK)
DecimalNumber.set_default(color=INK)
Brace.set_default(color=MUTED)


def T(s, size=32, color=INK, weight=NORMAL, font=FONT, **kw):
    return Text(s, font=font, font_size=size, color=color, weight=weight, **kw)


def M(s, size=44, color=INK, **kw):
    return MathTex(s, font_size=size, color=color, **kw)


def P(*lines, size=30, color=INK, align="left", spacing=0.75):
    return Paragraph(*lines, font=FONT, font_size=size, color=color, alignment=align, line_spacing=spacing)


class Clip(Scene):
    """Scene with one caption line at the bottom that is swapped between steps, and a hold at the end.
    Every animation is stretched by SPEED and every pause by PAUSE, so the pace is set in one place."""
    cap = None
    CAP_Y = -3.45
    HOLD = 5.0
    SPEED = 1.5
    PAUSE = 1.8

    def play(self, *args, **kw):
        if args and all(isinstance(a, Wait) for a in args):      # a pause: already scaled in wait()
            return super().play(*args, **kw)
        rt = kw.get("run_time")
        if rt is None:
            rt = max([getattr(a, "run_time", 1.0) for a in args if isinstance(a, Animation)] or [1.0])
        kw["run_time"] = rt * self.SPEED
        return super().play(*args, **kw)

    def wait(self, duration=1.0, **kw):
        return super().wait(duration * self.PAUSE, **kw)

    def caption(self, s, color=INK, size=40, run_time=0.5):
        new = T(s, size=size, color=color).move_to([0, self.CAP_Y, 0])
        if new.width > 13.6:
            new.scale_to_fit_width(13.6)
        if self.cap is None:
            self.add(new) if run_time == 0 else self.play(FadeIn(new, shift=0.15 * UP), run_time=run_time)
        else:
            self.play(FadeOut(self.cap, shift=0.15 * UP), FadeIn(new, shift=0.15 * UP), run_time=run_time)
        self.cap = new
        return new

    def hold(self):
        super().wait(self.HOLD)
