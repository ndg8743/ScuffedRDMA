#!/usr/bin/env python3
"""check2.py deck.pptx : content and structure checks of the built deck (titles, notes, alt text, links, wording)."""
import html, re, sys, zipfile
z = zipfile.ZipFile(sys.argv[1])
names = sorted([n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)], key=lambda n: int(re.findall(r"\d+", n)[0]))
N = len(names)
bad = []
words = pics = noalt = charts = gifs = links = backs = tables = stars = 0
star_slides = []
for n in names:
    k = int(re.findall(r"\d+", n)[0])
    x = z.read(n).decode()
    rels = z.read("ppt/slides/_rels/slide%d.xml.rels" % k).decode()
    if 'type="title"' not in x: bad.append((k, "no title placeholder"))
    t = re.search(r'type="title".*?</p:sp>', x, flags=re.S)
    title = html.unescape("".join(re.findall(r"<a:t>([^<]*)</a:t>", t.group(0)))) if t else ""
    if title.endswith("."): bad.append((k, "title ends with a period"))
    text = html.unescape(" ".join(re.findall(r"<a:t>([^<]*)</a:t>", x)))
    nt = z.read("ppt/notesSlides/notesSlide%d.xml" % k).decode() if "ppt/notesSlides/notesSlide%d.xml" % k in z.namelist() else ""
    notes = html.unescape(" ".join(re.findall(r"<a:t>([^<]*)</a:t>", nt)))
    if len(notes.split()) < 8: bad.append((k, "notes missing or very short"))
    alts = html.unescape(" ".join(re.findall(r'<p:cNvPr [^>]*descr="([^"]*)"', x)))
    for label, s in (("slide", text), ("notes", notes), ("alt text", alts)):
        for w in ("—", "–", "defect", "THIS THESIS", "1-bit", "TODO", "undefined", "NaN", "novel", "state-of-the-art", "cutting-edge", "leverage", "utilize", "seamless", "robust", "BIOS ID", "never", "always", "typed by hand", "not only", "Not a measurement"):
            if w in s: bad.append((k, "%s contains %r" % (label, w)))
        if re.search(r"\b(hydra|cosmos|chimera|cerberus)\b", s, flags=re.I): bad.append((k, label + " contains a host name"))
    # pictures and alt text
    for m in re.finditer(r"<p:pic>.*?</p:pic>", x, flags=re.S):
        pics += 1
        d = re.search(r'<p:cNvPr [^>]*descr="([^"]*)"', m.group(0))
        if not d or len(d.group(1)) < 10: noalt += 1; bad.append((k, "picture without alt text"))
    for m in re.finditer(r"<p:graphicFrame>.*?</p:graphicFrame>", x, flags=re.S):
        if "chart" in m.group(0):
            charts += 1
            d = re.search(r'<p:cNvPr [^>]*descr="([^"]*)"', m.group(0))
            if not d or len(d.group(1)) < 10: bad.append((k, "chart without alt text"))
        if "<a:tbl>" in m.group(0):
            tables += 1
            if 'firstRow="1"' not in m.group(0): bad.append((k, "table without header row flag"))
    gifs += len(re.findall(r'Target="\.\./media/[^"]*\.gif"', rels))
    # links to slides must resolve
    for rid in re.findall(r'<a:hlinkClick r:id="(rId\d+)"[^>]*action="ppaction://hlinksldjump"', x):
        links += 1
        tm = re.search(r'Id="%s"[^>]*Target="slide(\d+)\.xml"' % rid, rels) or re.search(r'Target="slide(\d+)\.xml"[^>]*Id="%s"' % rid, rels)
        if not tm or not (1 <= int(tm.group(1)) <= N): bad.append((k, "slide link does not resolve: " + rid))
    backs += x.count("hlinkshowjump?jump=lastslideviewed")
    if "<p:transition" not in x: bad.append((k, "no transition"))
    if re.search(r"</a:r><a:pPr", x): bad.append((k, "paragraph properties in the middle of a paragraph"))
    if "* " in text:
        stars += text.count("* "); star_slides.append(k)
    # smallest text on the slide outside the footer
    sizes = [int(s) for s in re.findall(r'<a:rPr [^>]*sz="(\d+)"', x)]
    small = [s for s in sizes if s < 1400 and s not in (1100, 1300)]
    if small: bad.append((k, "text below 14 pt: %s" % sorted(set(small))))
print("slides", N, "| pictures", pics, "(without alt: %d)" % noalt, "| charts", charts, "| tables", tables, "| gif relations", gifs, "| slide links", links, "| back buttons", backs)
print("media:", sorted(set(n.split("/")[-1].split(".")[-1] for n in z.namelist() if n.startswith("ppt/media/"))), len([n for n in z.namelist() if n.endswith(".gif")]), "gif files")
print("slides with star notes:", star_slides)
print("PROBLEMS:" if bad else "no problems found")
for b in bad: print("  ", b)
