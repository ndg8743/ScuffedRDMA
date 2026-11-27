"""Matrix drawn as a grid of cells; used by the matrix animations."""
from style import *


class Grid(VGroup):
    def __init__(self, values, cell=0.95, places=0, size=40, color=INK, fill=BG,
                 stroke=EDGE, numbers=True, stroke_width=2.5, **kw):
        super().__init__(**kw)
        self.vals = np.array(values, dtype=float)
        self.r, self.c = self.vals.shape
        self.cell = cell
        self.cells = VGroup()
        self.nums = VGroup()
        for i in range(self.r):
            for j in range(self.c):
                sq = Square(cell, stroke_color=stroke, stroke_width=stroke_width,
                            fill_color=fill, fill_opacity=1)
                sq.move_to([j * cell, -i * cell, 0])
                self.cells.add(sq)
                if numbers:
                    n = DecimalNumber(self.vals[i, j], num_decimal_places=places,
                                      font_size=size, color=color)
                    n.move_to(sq)
                    self.nums.add(n)
        self.add(self.cells)
        if numbers:
            self.add(self.nums)
        self.center()

    def cell_at(self, i, j):
        return self.cells[i * self.c + j]

    def num_at(self, i, j):
        return self.nums[i * self.c + j]

    def row(self, i):
        return VGroup(*[self.cell_at(i, j) for j in range(self.c)])

    def col(self, j):
        return VGroup(*[self.cell_at(i, j) for i in range(self.r)])

    def row_nums(self, i):
        return VGroup(*[self.num_at(i, j) for j in range(self.c)])


def frame(mob, color=NAVY, buff=0.0, width=7):
    return SurroundingRectangle(mob, color=color, buff=buff, stroke_width=width, corner_radius=0.05)


def head(sym, word, grid, size=48, wsize=28):
    """Symbol and a word above a grid."""
    s = M(sym, size=size)
    w = T(word, size=wsize, color=MUTED)
    g = VGroup(s, w).arrange(RIGHT, buff=0.22, aligned_edge=DOWN)
    g.next_to(grid, UP, buff=0.25)
    return g
