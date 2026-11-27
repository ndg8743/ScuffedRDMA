#!/usr/bin/env python3
"""Post-process the deck pptxgenjs wrote:
  1. a quick fade transition on every slide,
  2. Back buttons return to the slide last viewed,
  3. link buttons keep plain text (no underline),
  4. the first row of every table is marked as its header row,
  5. the theme colors and theme name of deck/theme.json are written into the theme part,
  6. two repairs for pptxgenjs output: folder entries are dropped, crossesAt="autoZero" becomes crosses.
  7. a paragraph keeps one set of paragraph properties (the slide library repeats them before every later run),
  8. the numbers of numbered lists use the body font,
  9. in a line chart the second and third series are dashed and dotted, so that the lines differ by more than color
     (the slide library takes one dash style for a whole chart).
Usage: post.py in.pptx out.pptx [theme.json]"""
import json, os, re, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
THEME = json.load(open(sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, "deck", "theme.json")))
SLOTS = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "hlink", "folHlink"]


def theme_xml(x):
    name = THEME["name"]
    scheme = '<a:clrScheme name="%s">' % name + "".join('<a:%s><a:srgbClr val="%s"/></a:%s>' % (k, THEME["colors"][k].upper(), k) for k in SLOTS) + "</a:clrScheme>"
    x = re.sub(r"<a:clrScheme\b.*?</a:clrScheme>", lambda m: scheme, x, count=1, flags=re.S)
    return re.sub(r'(<a:(?:theme|fontScheme)\b[^>]*?\bname=")[^"]*"', lambda m: m.group(1) + name + '"', x)


src, dst = sys.argv[1], sys.argv[2]
FADE = '<p:transition spd="fast"><p:fade/></p:transition>'
zin = zipfile.ZipFile(src)
zout = zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED)
n_tr = n_back = n_ppr = n_dash = 0
for item in zin.infolist():
    if item.filename.endswith("/"):
        continue
    data = zin.read(item.filename)
    if item.filename == "ppt/theme/theme1.xml":
        data = theme_xml(data.decode("utf-8")).encode("utf-8")
    elif item.filename.endswith(".xml") and b'<c:crossesAt val="autoZero"/>' in data:
        data = data.replace(b'<c:crossesAt val="autoZero"/>', b'<c:crosses val="autoZero"/>')
    if re.fullmatch(r"ppt/charts/chart\d+\.xml", item.filename) and b"<c:lineChart>" in data:
        x, k = data.decode("utf-8"), [0]
        def dash(m):
            style = ("solid", "dash", "sysDot")[min(k[0], 2)]
            k[0] += 1
            return m.group(0).replace('<a:prstDash val="solid"/>', '<a:prstDash val="%s"/>' % style, 1)
        x = re.sub(r"<c:ser>.*?</c:ser>", dash, x, flags=re.S)
        n_dash += k[0]
        data = x.encode("utf-8")
    if re.fullmatch(r"ppt/slides/slide\d+\.xml", item.filename):
        x = data.decode("utf-8")
        # 2. back buttons: the hyperlink of every shape named back-button becomes "last slide viewed"
        def fix(m):
            global n_back
            n_back += 1
            return m.group(1) + '<a:hlinkClick r:id="" action="ppaction://hlinkshowjump?jump=lastslideviewed" tooltip="Back to the slide you came from"/>'
        x = re.sub(r'(<p:cNvPr id="\d+" name="back-button">)<a:hlinkClick [^>]*/>', fix, x)
        # 3. a shape that is itself the link does not also need underlined link text inside it
        def clean_run(m):
            attrs, inner = m.group(1), m.group(2)
            if "hlinksldjump" not in inner:
                return m.group(0)
            attrs = attrs.replace(' u="sng"', "")
            inner = re.sub(r"<a:hlinkClick [^>]*hlinksldjump[^>]*>.*?</a:hlinkClick>", "", inner, flags=re.S)
            inner = re.sub(r"<a:hlinkClick [^>]*hlinksldjump[^>]*/>", "", inner)
            return "<a:rPr" + attrs + ">" + inner + "</a:rPr>"
        x = re.sub(r"<a:rPr((?:[^>/]|/(?!>))*)>(.*?)</a:rPr>", clean_run, x, flags=re.S)
        # 4. tables: mark the first row as the header row
        x = x.replace("<a:tblPr/>", '<a:tblPr firstRow="1"/>')
        # 7. paragraph properties belong at the start of a paragraph only
        x, k = re.subn(r"(</a:r>)<a:pPr\b[^>]*?(?:/>|>.*?</a:pPr>)", r"\1", x, flags=re.S)
        n_ppr += k
        # 8. numbers of numbered lists in the body font
        x = x.replace('<a:buFont typeface="+mj-lt"/>', '<a:buFont typeface="+mn-lt"/>')
        # 1. transition: after </p:clrMapOvr> if present, else after </p:cSld>; before <p:timing>
        if "<p:transition" not in x:
            if "</p:clrMapOvr>" in x:
                x = x.replace("</p:clrMapOvr>", "</p:clrMapOvr>" + FADE, 1)
            else:
                x = x.replace("</p:cSld>", "</p:cSld>" + FADE, 1)
            n_tr += 1
        data = x.encode("utf-8")
    # keep the GIFs stored, they do not compress
    if item.filename.endswith(".gif"):
        zout.writestr(item, data, compress_type=zipfile.ZIP_STORED)
    else:
        zout.writestr(item, data, compress_type=zipfile.ZIP_DEFLATED)
zout.close()
print("transitions added:", n_tr, " back buttons:", n_back, " repeated paragraph properties removed:", n_ppr, " line-chart series styled:", n_dash)
