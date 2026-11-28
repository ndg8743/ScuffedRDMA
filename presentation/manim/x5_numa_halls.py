"""X5: NUMA as two sorting halls joined by one corridor.

A hall stands for a NUMA node, the corridor for the interconnect, the loading bay for the network card (it is
attached to hall A), the shelf for the registered memory of the pool, and the worker for the thread that copies
a chunk off the shelf. Three rows, which are the three cases of section 5.6 of the thesis:
  1. shelf and worker in the hall of the bay: no trip goes through the corridor;
  2. shelf in the hall of the bay, worker in the other hall: every copy goes through it;
  3. shelf in the other hall: every delivery goes through it, wherever the worker stands.
The last caption says how the hall of the shelf is chosen today: it is the hall in which the worker stands when
the shelf is first filled.

The three floor plans are on the screen from the first frame."""
from style import *
from figures import person, parcel, entry, legend

XL = -6.98
YC = [1.95, 0.10, -1.75]               # centre of each row
BAY, HA, CO, HB = (-6.98, -6.55), (-6.55, -3.75), (-3.75, -3.05), (-3.05, -0.25)      # left and right edge
HH, CH = 0.95, 0.30                    # height of a hall and of the corridor
XR = 0.3                               # the text at the right
CASES = [
    dict(title="Shelf and worker in the hall of the loading bay", shelf=-5.25, worker=-4.25,
         a="no trip through the corridor", b="everything stays in hall A"),
    dict(title="Shelf in the hall of the bay, worker in the other hall", shelf=-5.25, worker=-1.0,
         a="every copy crosses", b="the worker fetches through the corridor"),
    dict(title="Shelf in the other hall", shelf=-1.85, worker=-0.8,
         a="every delivery crosses", b="wherever the worker stands"),
]


class X5NumaHalls(Clip):
    def construct(self):
        l1 = legend([("hall", "NUMA node"), ("corridor", "interconnect"), ("loading bay", "network card")], 3.68)
        l2 = VGroup(entry("shelf", "registered memory", XL, 3.16), entry("worker", "thread that copies", -1.3, 3.16))
        self.add(l1, l2)

        rows = []
        for k, c in enumerate(CASES):
            yh = YC[k] - 0.15
            mid = lambda p: (p[0] + p[1]) / 2
            hall = lambda p: Rectangle(width=p[1] - p[0], height=HH, stroke_color=INK, stroke_width=3, fill_color=PANEL, fill_opacity=1).move_to([mid(p), yh, 0])
            corr = Rectangle(width=CO[1] - CO[0], height=CH, stroke_width=0, fill_color=PANEL, fill_opacity=1).move_to([mid(CO), yh, 0])
            walls = VGroup(Line([CO[0], yh + CH / 2, 0], [CO[1], yh + CH / 2, 0], color=INK, stroke_width=3),
                           Line([CO[0], yh - CH / 2, 0], [CO[1], yh - CH / 2, 0], color=INK, stroke_width=3))
            bay = Rectangle(width=BAY[1] - BAY[0], height=0.5, stroke_color=INK, stroke_width=3, fill_color=BG, fill_opacity=1).move_to([mid(BAY), yh, 0])
            doors = VGroup(*[Rectangle(width=0.09, height=h, stroke_width=0, fill_color=col, fill_opacity=1).move_to([x, yh, 0])
                             for x, h, col in [(HA[1], CH - 0.05, PANEL), (HB[0], CH - 0.05, PANEL), (HA[0], 0.44, BG)]])
            names = VGroup(T("A", size=28, color=MUTED, weight=BOLD).move_to([HA[0] + 0.25, yh + HH / 2 - 0.24, 0]),
                           T("B", size=28, color=MUTED, weight=BOLD).move_to([HB[0] + 0.25, yh + HH / 2 - 0.24, 0]))
            xs, xw = c["shelf"], c["worker"]
            shelf = VGroup(Rectangle(width=0.84, height=0.5, stroke_color=INK, stroke_width=3, fill_color=BG, fill_opacity=1).move_to([xs, yh, 0]),
                           *[Line([xs + d, yh - 0.25, 0], [xs + d, yh + 0.25, 0], color=INK, stroke_width=2.5) for d in (-0.14, 0.14)])
            feet = yh - HH / 2 + 0.07
            worker = person(NAVY, 0.62).shift([xw, feet, 0])
            load = parcel(0.2).move_to([mid(BAY), yh, 0])
            label = T(c["title"], size=28, color=NAVY if k == 0 else MUTED).move_to([XL, YC[k] + 0.62, 0], aligned_edge=LEFT)
            self.add(hall(HA), hall(HB), corr, walls, bay, doors, names, shelf, worker, load, label)
            rows.append(dict(yh=yh, corr=corr, walls=walls, xs=xs, xw=xw, hand=np.array([xw - 0.24, feet + 0.3, 0]), label=label))

        def right(k):
            r = rows[k]
            return VGroup(T(CASES[k]["a"], size=30, weight=BOLD).move_to([XR, r["yh"] + 0.22, 0], aligned_edge=LEFT),
                          T(CASES[k]["b"], size=28, color=MUTED).move_to([XR, r["yh"] - 0.24, 0], aligned_edge=LEFT))

        def mark(k):
            """The corridor of row k is in use."""
            r = rows[k]
            return [r["corr"].animate.set_fill(AMBER, 1), r["walls"].animate.set_color(NAVY).set_stroke(width=5)]

        def round_(k, first):
            """One parcel: from the bay to the shelf, then off the shelf to the worker."""
            r = rows[k]
            yh, xs = r["yh"], r["xs"]
            p = parcel(0.2).move_to([BAY[1] - 0.1, yh, 0]).set_z_index(3)
            cross_in = xs > CO[1]                       # the shelf is in hall B
            cross_out = (r["xw"] > CO[1]) != cross_in  # the worker is in the other hall than the shelf
            sp = 1.0 if first else 0.7
            self.add(p)
            self.play(p.animate.move_to([xs, yh, 0]), *(mark(k) if cross_in and first else []), run_time=(1.5 if cross_in else 0.9) * sp)
            if cross_out:
                path = VMobject().set_points_as_corners([[xs, yh, 0], [CO[0], yh, 0], [CO[1], yh, 0], r["hand"]])
                self.play(MoveAlongPath(p, path), *(mark(k) if first else []), run_time=1.5 * sp)
            else:
                self.play(p.animate.move_to(r["hand"]), run_time=0.7 * sp)
            self.play(FadeOut(p), run_time=0.25)

        # 1. everything in the hall of the bay
        self.caption("Two halls, one corridor, and the loading bay is in hall A", run_time=0)
        self.wait(1.6)
        self.caption("Shelf and worker beside the bay: no trip leaves the hall")
        round_(0, True)
        round_(0, False)
        self.play(FadeIn(right(0)), run_time=0.4)
        self.wait(1.0)

        # 2. the worker in the other hall
        self.caption("Worker in the other hall: every copy goes through the corridor")
        self.play(rows[0]["label"].animate.set_color(MUTED), rows[1]["label"].animate.set_color(NAVY), run_time=0.5)
        round_(1, True)
        round_(1, False)
        self.play(FadeIn(right(1)), run_time=0.4)
        self.wait(1.0)

        # 3. the shelf in the other hall
        self.caption("Shelf in the other hall: every delivery goes through the corridor")
        self.play(rows[1]["label"].animate.set_color(MUTED), rows[2]["label"].animate.set_color(NAVY), run_time=0.5)
        round_(2, True)
        round_(2, False)
        self.play(FadeIn(right(2)), run_time=0.4)
        self.wait(1.2)

        # 4. how the hall of the shelf is chosen today
        self.caption("Today the shelf goes up in the hall where the worker first fills it", color=NAVY)
        self.play(rows[2]["label"].animate.set_color(MUTED), run_time=0.4)
        self.hold()
