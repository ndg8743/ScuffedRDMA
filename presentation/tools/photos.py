#!/usr/bin/env python3
"""photos.py <folder of Update 1>  ->  assets/photos/*.jpg|png and manifest.json

Prepares the pictures of the first update report (Updates/Update1-HardwareSetup in the repository) for the slides:
orientation applied, cropped where a part of the picture is enough, reduced to at most 2400 pixels, and written
without camera metadata. The crop boxes are in pixels (left, top, right, bottom) of the original file, or of the
file after the small rotation given as an optional fourth value (degrees, counterclockwise as in Pillow), which
levels a screen that was photographed at an angle."""
import json, os, sys
from PIL import Image, ImageOps

Image.MAX_IMAGE_PIXELS = None
SRC = sys.argv[1] if len(sys.argv) > 1 else "."
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "photos")
os.makedirs(OUT, exist_ok=True)

# name: (source file, crop box or None, output format)
PICS = {
    "towers": ("towers-initial-setup.jpg", None, "jpg"),
    "v100_installed": ("v100-gpus-installed.jpg", None, "jpg"),
    "staging": ("hardware-staging-v100s.jpg", (30, 1060, 950, 1817), "jpg"),
    "vendor_firmware_list": ("bios-official-versions.png", (318, 140, 1541, 804), "png"),
    # the System Information block of the setup screen (left two thirds of the photograph), leveled by 1.1 degrees.
    # The picture ends under the line "BIOS Date": the line "BIOS ID" below it is not needed on the slide.
    "firmware_f24": ("bios-custom-f24-rebar.jpg", (10, 104, 1528, 412), "jpg", -1.1),
    # the lower table of the status report (GPU status)
    "server4_status": ("specs-proxmox-server.png", (0, 418, 900, 817), "jpg"),
}
manifest = {}
for name, spec in PICS.items():
    src, box, fmt = spec[:3]
    turn = spec[3] if len(spec) > 3 else 0
    im = ImageOps.exif_transpose(Image.open(os.path.join(SRC, src))).convert("RGB")
    if turn:
        im = im.rotate(turn, resample=Image.BICUBIC, expand=False)
    if box:
        im = im.crop(box)
    if im.width > 2400:
        im = im.resize((2400, round(im.height * 2400 / im.width)), Image.LANCZOS)
    path = os.path.join(OUT, name + "." + fmt)
    clean = Image.new("RGB", im.size)          # a new image carries no metadata of the camera
    clean.paste(im)
    if fmt == "jpg":
        clean.save(path, quality=88, optimize=True)
    else:
        clean.save(path, optimize=True)
    manifest[name] = {"file": name + "." + fmt, "w": im.width, "h": im.height, "source": src, "crop": box, "rotation": turn}
    print(name, im.size, os.path.getsize(path))
json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
