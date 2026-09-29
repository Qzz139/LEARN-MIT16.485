"""Compose the Lab0 report figures from the saved program outputs.

Run after calibrate_phone.py and stereo_depth.py (needs Pillow and macOS Arial):
    python3.9 lab0/reports/build_figures.py
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(parents=True, exist_ok=True)
INK = "#242824"
RED = "#aa533f"
TEAL = "#257b83"
PAPER = "#fbfaf6"


def font(size, bold=False):
    name = "Arial Bold.ttf" if bold else "Arial.ttf"
    path = Path("/System/Library/Fonts/Supplemental") / name
    return ImageFont.truetype(str(path), size)


def panel_image(source, width, height):
    picture = Image.open(source).convert("RGB")
    return ImageOps.contain(picture, (width, height), Image.Resampling.LANCZOS)


def calibration_figures():
    result = ROOT / "results/calibration"
    summary = json.loads((result / "summary.json").read_text())
    records = summary["per_view"]
    names = {item["file"]: (i + 1, item["rms_px"]) for i, item in enumerate(records)}

    # Show a low-error image, a tilted image, and the high-error view.
    selected = ["IMG_2298.jpg", "IMG_2300.jpg", "IMG_2312.jpg"]
    canvas = Image.new("RGB", (1650, 460), PAPER)
    draw = ImageDraw.Draw(canvas)
    for col, name in enumerate(selected):
        number, error = names[name]
        picture = panel_image(result / "corners" / f"{number:03d}.png", 532, 380)
        x = col * 550 + (550 - picture.width) // 2
        canvas.paste(picture, (x, 4))
        draw.text((col * 550 + 12, 401),
                  f"{name}   RMS {error:.3f} px",
                  fill=INK, font=font(23))
    canvas.save(OUT / "calibration_examples.jpg", quality=91)

    original = Image.open(result / "before_after.png").convert("RGB")
    width = original.width // 2
    before = ImageOps.contain(original.crop((0, 0, width, original.height)),
                              (780, 585), Image.Resampling.LANCZOS)
    after = ImageOps.contain(original.crop((width, 0, original.width, original.height)),
                             (780, 585), Image.Resampling.LANCZOS)
    comparison = Image.new("RGB", (1600, 650), PAPER)
    comparison.paste(before, (10, 45))
    comparison.paste(after, (810, 45))
    draw = ImageDraw.Draw(comparison)
    draw.text((10, 8), "Original image", fill=INK, font=font(29, bold=True))
    draw.text((810, 8), "After undistortion", fill=INK, font=font(29, bold=True))
    comparison.save(OUT / "calibration_undistortion.jpg", quality=90)

    chart = Image.new("RGB", (1250, 700), PAPER)
    draw = ImageDraw.Draw(chart)
    draw.text((30, 12), "Reprojection RMS by image", fill=INK, font=font(32, bold=True))
    sorted_records = sorted(records, key=lambda record: record["rms_px"], reverse=True)
    x0, width, row_height = 215, 920, 30
    for i, record in enumerate(sorted_records):
        y = 64 + i * row_height
        error = record["rms_px"]
        color = RED if record["file"] == "IMG_2312.jpg" else TEAL
        draw.text((30, y + 2), record["file"].replace(".jpg", ""), fill=INK, font=font(23))
        draw.rectangle((x0, y + 5, x0 + int(width * error / 2.5), y + 24), fill=color)
        draw.text((x0 + int(width * error / 2.5) + 12, y + 1),
                  f"{error:.3f}", fill=INK, font=font(22))
    chart.save(OUT / "calibration_rms.png")


def stereo_figures():
    stereo = ROOT / "results/stereo"
    left = panel_image(ROOT / "data/stereo/aloeL.jpg", 641, 555)
    pair = Image.open(stereo / "rectified_pair_check.png").convert("RGB")
    pair.save(OUT / "stereo_pair.jpg", quality=92)

    maps = Image.new("RGB", (1322, 615), PAPER)
    draw = ImageDraw.Draw(maps)
    draw.text((5, 8), "Disparity (px)", fill=INK, font=font(28, bold=True))
    draw.text((666, 8), "Relative depth (assumed baseline units)",
              fill=INK, font=font(28, bold=True))
    maps.paste(Image.open(stereo / "disparity.png").convert("RGB"), (5, 45))
    maps.paste(Image.open(stereo / "depth_preview.png").convert("RGB"), (666, 45))
    maps.save(OUT / "stereo_maps.jpg", quality=92)

    rois = Image.new("RGB", (641, 620), PAPER)
    rois.paste(left, (0, 0))
    draw = ImageDraw.Draw(rois)
    areas = [
        ("B", (80, 40, 180, 180), TEAL),
        ("L", (350, 230, 430, 350), RED),
        ("P", (370, 410, 510, 530), "#a6751f"),
    ]
    for label, box, color in areas:
        draw.rectangle(box, outline=color, width=5)
        draw.rounded_rectangle((box[0] + 4, box[1] + 4, box[0] + 38, box[1] + 38),
                               radius=4, fill=color)
        draw.text((box[0] + 12, box[1] + 6), label, fill="white", font=font(24, bold=True))
    draw.text((12, 570), "B  background     L  leaf/core     P  pot",
              fill=INK, font=font(23))
    rois.save(OUT / "stereo_rois.jpg", quality=92)


if __name__ == "__main__":
    calibration_figures()
    stereo_figures()
    print("Report figures:", OUT)
