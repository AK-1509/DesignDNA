"""Generate a small synthetic design corpus (magazine, report, portfolio image, brief, deck) for tests."""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image, ImageDraw

VERMILION = (0xE4 / 255, 0x57 / 255, 0x2E / 255)
NAVY = (0x1D / 255, 0x35 / 255, 0x57 / 255)
STEEL = (0x45 / 255, 0x7B / 255, 0x9D / 255)
CREAM = (0xF6 / 255, 0xF1 / 255, 0xE7 / 255)
INK = (0x1A / 255, 0x1A / 255, 0x1A / 255)

BODY = ("Design systems are distilled from practice rather than invented from nothing. The editors kept the grid "
        "strict and the margins wide, so photographs could run full bleed while the text held its measure. ")


def photo(path: Path, w=800, h=600, seed=1):
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:h, 0:w]
    r = (0.55 + 0.35 * np.sin(x / 90 + seed)) * 255
    g = (0.45 + 0.25 * np.cos(y / 70)) * 255
    b = (0.40 + 0.3 * np.sin((x + y) / 120)) * 255
    arr = np.stack([r, g, b], -1) + rng.normal(0, 8, (h, w, 3))
    Image.fromarray(np.clip(arr, 0, 255).astype("uint8")).save(path)


def magazine(path: Path, img: Path):
    doc = pymupdf.open()
    W, H = 595, 842
    for i in range(6):
        p = doc.new_page(width=W, height=H)
        p.draw_rect(p.rect, color=None, fill=CREAM)
        p.insert_text((48, 40), "SPRING ISSUE · CULTURE", fontname="helv", fontsize=7, color=INK)
        if i % 2 == 0:
            p.insert_image(pymupdf.Rect(0, 60, W, 400), filename=str(img))
            y0 = 440
        else:
            p.draw_rect(pymupdf.Rect(48, 60, W - 48, 64), color=None, fill=VERMILION)
            y0 = 110
        p.insert_text((48, y0), "The Quiet Grid", fontname="tibo", fontsize=44, color=INK)
        p.insert_text((48, y0 + 30), "How restraint became a style", fontname="tiro", fontsize=16, color=VERMILION)
        col_w = (W - 96 - 18) / 2
        for c in range(2):
            x = 48 + c * (col_w + 18)
            rect = pymupdf.Rect(x, y0 + 50, x + col_w, H - 60)
            rc = p.insert_textbox(rect, BODY * 12, fontname="tiro", fontsize=9.5, lineheight=1.3, color=INK)
            n = 11
            while rc < 0 and n > 1:  # text must fit or PyMuPDF writes nothing
                rc = p.insert_textbox(rect, BODY * n, fontname="tiro", fontsize=9.5, lineheight=1.3, color=INK)
                n -= 1
        p.insert_text((48, H - 30), f"PAGE {i + 1}", fontname="helv", fontsize=7, color=INK)
    doc.set_metadata({"title": "Spring Issue"})
    doc.save(path)


def report(path: Path):
    doc = pymupdf.open()
    W, H = 612, 792
    for i in range(4):
        p = doc.new_page(width=W, height=H)
        p.insert_text((72, 90), "Annual Findings 2026", fontname="hebo", fontsize=26, color=NAVY)
        p.insert_text((72, 120), "SECTION " + str(i + 1), fontname="helv", fontsize=8, color=STEEL)
        p.insert_textbox(pymupdf.Rect(72, 140, W - 72, 420), BODY * 8, fontname="helv", fontsize=10,
                         lineheight=1.4, color=INK)
        for j, hgt in enumerate((120, 180, 90, 150)):
            p.draw_rect(pymupdf.Rect(90 + j * 110, 700 - hgt, 160 + j * 110, 700), color=None,
                        fill=VERMILION if j % 2 == 0 else STEEL)
    doc.save(path)


def portfolio(path: Path):
    im = Image.new("RGB", (1600, 1000), (246, 241, 231))
    d = ImageDraw.Draw(im)
    d.rectangle([80, 80, 760, 920], fill=(228, 87, 46))
    d.rectangle([840, 80, 1520, 480], fill=(29, 53, 87))
    d.rectangle([840, 520, 1520, 920], fill=(26, 26, 26))
    im.save(path)


def brief(path: Path):
    path.write_text("""# Creative brief — Meridian Press rebrand

Client: Meridian Press, an independent publisher of long-form essays.
Audience: curious readers, 25–55, who read on phones at night and on paper at weekends.

## Goals
- Feel editorial and confident, never corporate.
- Make long reading comfortable on screen.

## Brand colours
- Primary brand colour: Vermilion #E4572E
- Secondary colour: Navy #1D3557 (used for headlines in reports)
- Background: warm paper #F6F1E7

## Typography
Headlines are set in Playfair Display; body copy is set in Source Serif 4.

## Tone
Warm, precise, a little wry.
""", encoding="utf-8")


def deck(path: Path):
    theme = """<?xml version="1.0"?><a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Meridian">
<a:themeElements><a:clrScheme name="Meridian">
<a:dk1><a:srgbClr val="1A1A1A"/></a:dk1><a:lt1><a:srgbClr val="F6F1E7"/></a:lt1>
<a:dk2><a:srgbClr val="1D3557"/></a:dk2><a:lt2><a:srgbClr val="EDE6D6"/></a:lt2>
<a:accent1><a:srgbClr val="E4572E"/></a:accent1><a:accent2><a:srgbClr val="457B9D"/></a:accent2>
<a:accent3><a:srgbClr val="A8DADC"/></a:accent3><a:accent4><a:srgbClr val="F1C453"/></a:accent4>
<a:accent5><a:srgbClr val="2A9D8F"/></a:accent5><a:accent6><a:srgbClr val="6D597A"/></a:accent6>
<a:hlink><a:srgbClr val="E4572E"/></a:hlink><a:folHlink><a:srgbClr val="6D597A"/></a:folHlink>
</a:clrScheme><a:fontScheme name="Meridian"><a:majorFont><a:latin typeface="Playfair Display"/></a:majorFont>
<a:minorFont><a:latin typeface="Source Serif 4"/></a:minorFont></a:fontScheme></a:themeElements></a:theme>"""
    slide = """<?xml version="1.0"?><p:sld xmlns:p="p" xmlns:a="a"><p:cSld><p:spTree>
<a:p><a:r><a:rPr sz="4400"><a:latin typeface="Playfair Display"/></a:rPr><a:t>Meridian Press</a:t></a:r></a:p>
<a:p><a:r><a:rPr sz="1800"/><a:t>Essays worth the evening.</a:t></a:r></a:p>
<a:p><a:r><a:rPr sz="1800"/><a:t>Long-form, carefully set.</a:t></a:r></a:p>
</p:spTree></p:cSld></p:sld>"""
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("ppt/theme/theme1.xml", theme)
        z.writestr("ppt/slides/slide1.xml", slide)


def main(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    img = out / "_photo.png"
    photo(img)
    magazine(out / "meridian-magazine-spring.pdf", img)
    report(out / "annual-report-2026.pdf")
    portfolio(out / "studio-portfolio.png")
    brief(out / "meridian-brief.md")
    deck(out / "pitch-deck.pptx")
    img.unlink()
    print(f"fixtures in {out}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "fixtures")
