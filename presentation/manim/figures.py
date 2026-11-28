"""Small pictograms shared by the metaphor animations (x1 to x5)."""
from style import *


def person(color, scale=1.0):
    """A standing figure 0.93 high (times scale) with its feet at the origin."""
    sw = 5
    g = VGroup(
        Circle(radius=0.13, stroke_width=0, fill_color=color, fill_opacity=1).move_to([0, 0.80, 0]),
        Line([0, 0.67, 0], [0, 0.30, 0], color=color, stroke_width=sw),
        Line([0, 0.30, 0], [-0.13, 0, 0], color=color, stroke_width=sw),
        Line([0, 0.30, 0], [0.13, 0, 0], color=color, stroke_width=sw),
        Line([0, 0.58, 0], [-0.13, 0.34, 0], color=color, stroke_width=sw),
        Line([0, 0.58, 0], [0.13, 0.34, 0], color=color, stroke_width=sw))
    g.scale(scale, about_point=ORIGIN)
    return g


def parcel(side=0.2):
    """One parcel: a square in the blue of the bulk class."""
    return Square(side, stroke_color=COLD, stroke_width=2.5, fill_color=COLDF, fill_opacity=1)


def stack(cols=2, rows=3, side=0.2):
    """A stack of parcels with its lower left corner at the origin."""
    return VGroup(*[parcel(side).move_to([side * (c + 0.5), side * (r + 0.5), 0]) for r in range(rows) for c in range(cols)])


def envelope(w=0.34, h=0.22):
    """A letter: a small envelope in the orange of the urgent class."""
    r = Rectangle(width=w, height=h, stroke_color=HOT, stroke_width=2.5, fill_color=HOTF, fill_opacity=1)
    v = VMobject(color=HOT, stroke_width=2.5).set_points_as_corners([[-w / 2, h / 2, 0], [0, -0.01, 0], [w / 2, h / 2, 0]])
    return VGroup(r, v)


def check(color=NAVY, s=1.0):
    """A check mark about 0.25 wide."""
    return VMobject(color=color, stroke_width=5).set_points_as_corners([[-0.12 * s, 0.01 * s, 0], [-0.04 * s, -0.09 * s, 0], [0.13 * s, 0.12 * s, 0]])


def entry(word, meaning, x, y, size=28):
    """One line of a legend: the word of the picture in bold navy, then what it stands for."""
    t = MarkupText('<span foreground="%s"><b>%s</b></span>  =  %s' % (NAVY, word, meaning), font=FONT, font_size=size, color=INK)
    return t.move_to([x, y, 0], aligned_edge=LEFT)


def legend(items, y, x0=-6.98, x1=6.98, size=28):
    """Entries of a legend spread over one line from x0 to x1. items: [(word, meaning), ...]"""
    es = [entry(w, m, 0, y, size) for w, m in items]
    free = (x1 - x0) - sum(e.width for e in es)
    gap = free / max(1, len(es) - 1) if len(es) > 1 else 0
    x = x0
    for e in es:
        e.move_to([x, y, 0], aligned_edge=LEFT)
        x += e.width + gap
    return VGroup(*es)
