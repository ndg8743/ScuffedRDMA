"""Shared look for the README animations (Manim Community 0.19+).

Colors carry meaning in every scene:
  HOT    orange  latency-critical: token ids, metadata, decode KV deltas, credits
  COLD   blue    bulk: prefill KV, weights
  SPILL  violet  storage tier (NVMe, GPFS)
  OK     green   decisions taken, checks passed
  BAD    rose    stalls, failures, issues
"""
from __future__ import annotations

from manim import (
    DOWN, LEFT, RIGHT, UP, ORIGIN, UL, UR, DL, DR,
    Arrow, FadeIn, FadeOut, Line, Rectangle, RoundedRectangle, Scene, Text, VGroup,
    config, rate_functions,
)

BG = "#0b1020"
PANEL = "#141c2f"
EDGE = "#334155"
TEXT = "#e2e8f0"
MUTED = "#94a3b8"
HOT = "#f97316"
COLD = "#38bdf8"
SPILL = "#a78bfa"
OK = "#34d399"
BAD = "#f43f5e"
GOLD = "#facc15"

FONT = "Inter"
MONO = "DejaVu Sans Mono"

config.background_color = BG


def T(s: str, size: float = 22, color: str = TEXT, weight: str = "NORMAL", mono: bool = False, **kw) -> Text:
    """Text at a font size that reads at 800 px wide."""
    return Text(s, font=MONO if mono else FONT, color=color, weight=weight, font_size=size, **kw)


def TC(s: str, size: float = 22, color: str = TEXT, weight: str = "NORMAL", mono: bool = False,
       buff: float = 0.06) -> VGroup:
    """Multi-line text with each line centered."""
    return VGroup(*[T(line, size, color, weight, mono) for line in s.split("\n")]).arrange(DOWN, buff=buff)


def box(w: float, h: float, color: str = EDGE, fill: str = PANEL, label: str | None = None,
        size: float = 20, label_color: str = TEXT, r: float = 0.12, opacity: float = 1.0,
        weight: str = "NORMAL") -> VGroup:
    rect = RoundedRectangle(width=w, height=h, corner_radius=r, stroke_color=color, stroke_width=2,
                            fill_color=fill, fill_opacity=opacity)
    g = VGroup(rect)
    if label:
        t = TC(label, size, label_color, weight=weight)
        if t.width > w - 0.2:
            t.scale_to_fit_width(w - 0.2)
        t.move_to(rect)
        g.add(t)
    return g


def packet(color: str, w: float = 0.32, h: float = 0.32, label: str | None = None, size: float = 14) -> VGroup:
    r = RoundedRectangle(width=w, height=h, corner_radius=min(0.06, h / 3), stroke_width=0,
                         fill_color=color, fill_opacity=1)
    g = VGroup(r)
    if label:
        t = T(label, size, BG, weight="BOLD")
        if t.width > w - 0.08:
            t.scale_to_fit_width(max(w - 0.08, 0.05))
        t.move_to(r)
        g.add(t)
    return g


def arrow(a, b, color: str = MUTED, buff: float = 0.1, sw: float = 3, tip: float = 0.18) -> Arrow:
    return Arrow(a, b, buff=buff, color=color, stroke_width=sw, max_tip_length_to_length_ratio=0.25,
                 tip_length=tip)


class Captioned(Scene):
    """Scene with a section tag (top left) and a subtitle line at the bottom."""

    tag = ""

    def setup(self):
        self._cap = None
        if self.tag:
            t = T(self.tag, 18, MUTED, weight="MEDIUM").to_corner(UL, buff=0.3)
            bar = Line(t.get_left() + DOWN * 0.22, t.get_right() + DOWN * 0.22, color=HOT, stroke_width=3)
            self.add(t, bar)

    def caption(self, s: str, wait: float = 0.0, size: float = 21, color: str = TEXT):
        new = T(s, size, color)
        if new.width > config.frame_width - 0.8:
            new.scale_to_fit_width(config.frame_width - 0.8)
        new.to_edge(DOWN, buff=0.28)
        anims = [FadeIn(new, shift=UP * 0.1)]
        if self._cap is not None:
            anims.insert(0, FadeOut(self._cap, shift=UP * 0.1))
        self.play(*anims, run_time=0.5)
        self._cap = new
        if wait:
            self.wait(wait)

    def clear_caption(self):
        if self._cap is not None:
            self.play(FadeOut(self._cap), run_time=0.3)
            self._cap = None


def wrap(s: str, width: int = 70) -> str:
    import textwrap
    return "\n".join(textwrap.wrap(s, width))
